import os
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

SUGAR_THRESHOLD_HIGH = 10
SODIUM_THRESHOLD_HIGH = 1000
FAT_THRESHOLD_HIGH = 20


def load_data():
    profiles = pd.read_csv(os.path.join(DATA_DIR, 'elderly_profiles.csv'), encoding='utf-8-sig')
    meals = pd.read_csv(os.path.join(DATA_DIR, 'meal_nutrition.csv'), encoding='utf-8-sig')
    orders = pd.read_csv(os.path.join(DATA_DIR, 'order_records.csv'), encoding='utf-8-sig')
    pickup = pd.read_csv(os.path.join(DATA_DIR, 'pickup_methods.csv'), encoding='utf-8-sig')
    return profiles, meals, orders, pickup


def get_dietary_restrictions(profiles):
    restrictions = []
    for _, row in profiles.iterrows():
        elder_restrictions = set()
        chronic = str(row['慢病标签'])
        doctor_note = str(row['医生备注']) if pd.notna(row['医生备注']) else ''

        if '糖尿病' in chronic:
            elder_restrictions.add('高糖限制')
        if '高血压' in chronic:
            elder_restrictions.add('高盐限制')

        if '低糖' in doctor_note or '糖尿病' in doctor_note:
            elder_restrictions.add('高糖限制')
        if '低盐' in doctor_note or '高血压' in doctor_note:
            elder_restrictions.add('高盐限制')
        if '低脂' in doctor_note:
            elder_restrictions.add('高脂限制')

        restrictions.append({
            '老人ID': row['老人ID'],
            '姓名': row['姓名'],
            '年龄': row['年龄'],
            '所属社区': row['所属社区'],
            '慢病标签': row['慢病标签'],
            '医生备注': row['医生备注'],
            '忌口类型': '、'.join(sorted(elder_restrictions)) if elder_restrictions else '无特殊忌口'
        })

    return pd.DataFrame(restrictions)


def classify_restriction_violation(row, restrictions_dict):
    elder_id = row['老人ID']
    elder_info = restrictions_dict.get(elder_id, {})
    restrictions = elder_info.get('忌口类型', '')

    violations = []
    sugar = row['糖(g)']
    sodium = row['钠(mg)']
    fat = row['脂肪(g)']

    if '高糖限制' in restrictions and sugar >= SUGAR_THRESHOLD_HIGH:
        violations.append(f'高糖(糖{sugar}g)')
    if '高盐限制' in restrictions and sodium >= SODIUM_THRESHOLD_HIGH:
        violations.append(f'高盐(钠{sodium}mg)')
    if '高脂限制' in restrictions and fat >= FAT_THRESHOLD_HIGH:
        violations.append(f'高脂(脂肪{fat}g)')

    return '、'.join(violations) if violations else ''


def analyze_dietary_restriction(profiles, meals, orders, pickup):
    restrictions = get_dietary_restrictions(profiles)
    restrictions_dict = restrictions.set_index('老人ID').to_dict('index')

    high_risk_meals = meals.copy()
    high_risk_meals['高糖标识'] = high_risk_meals['糖(g)'] >= SUGAR_THRESHOLD_HIGH
    high_risk_meals['高盐标识'] = high_risk_meals['钠(mg)'] >= SODIUM_THRESHOLD_HIGH
    high_risk_meals['高脂标识'] = high_risk_meals['脂肪(g)'] >= FAT_THRESHOLD_HIGH

    merged = orders.merge(profiles[['老人ID', '姓名', '年龄', '所属社区', '慢病标签', '医生备注']], on='老人ID', how='left')
    merged = merged.merge(meals[['餐品ID', '餐品名称', '糖(g)', '钠(mg)', '脂肪(g)']], on='餐品ID', how='left')
    merged = merged.merge(pickup[['老人ID', '默认取餐点']], on='老人ID', how='left')
    merged = merged.rename(columns={'默认取餐点': '所属食堂'})

    merged['忌口违规类型'] = merged.apply(lambda r: classify_restriction_violation(r, restrictions_dict), axis=1)

    violation_records = merged[merged['忌口违规类型'] != ''].copy()
    violation_records = violation_records.sort_values(['下单日期', '所属食堂', '老人ID'])

    detail_cols = [
        '订单ID', '老人ID', '姓名', '年龄', '所属社区', '所属食堂',
        '慢病标签', '医生备注', '餐品ID', '餐品名称',
        '糖(g)', '钠(mg)', '脂肪(g)', '忌口违规类型',
        '下单日期', '餐次', '订单来源', '订餐渠道', '退餐原因'
    ]
    violation_detail = violation_records[detail_cols].copy()

    violation_detail.to_csv(os.path.join(OUTPUT_DIR, '6_忌口匹配分析明细.csv'), index=False, encoding='utf-8-sig')

    source_stats = violation_records.groupby(['订单来源', '忌口违规类型']).agg(
        违规订单数=('订单ID', 'count'),
        涉及老人数=('老人ID', 'nunique'),
    ).reset_index().sort_values(['订单来源', '违规订单数'], ascending=[True, False])

    canteen_stats = violation_records.groupby('所属食堂').agg(
        违规订单数=('订单ID', 'count'),
        涉及老人数=('老人ID', 'nunique'),
        高糖违规数=('忌口违规类型', lambda x: x.str.contains('高糖').sum()),
        高盐违规数=('忌口违规类型', lambda x: x.str.contains('高盐').sum()),
        高脂违规数=('忌口违规类型', lambda x: x.str.contains('高脂').sum()),
    ).reset_index().sort_values('违规订单数', ascending=False)

    date_stats = violation_records.groupby('下单日期').agg(
        违规订单数=('订单ID', 'count'),
        涉及老人数=('老人ID', 'nunique'),
    ).reset_index().sort_values('下单日期')

    channel_stats = violation_records.groupby(['订餐渠道', '订单来源']).agg(
        违规订单数=('订单ID', 'count'),
    ).reset_index().sort_values(['订餐渠道', '违规订单数'], ascending=[True, False])

    has_refund_mask = violation_records['退餐原因'].notna() & (violation_records['退餐原因'] != '')
    refund_violation = violation_records[has_refund_mask].groupby(['退餐原因', '忌口违规类型']).agg(
        退餐订单数=('订单ID', 'count'),
    ).reset_index().sort_values('退餐订单数', ascending=False)

    source_stats.to_csv(os.path.join(OUTPUT_DIR, '6_1_按订单来源统计.csv'), index=False, encoding='utf-8-sig')
    canteen_stats.to_csv(os.path.join(OUTPUT_DIR, '6_2_按食堂统计.csv'), index=False, encoding='utf-8-sig')
    date_stats.to_csv(os.path.join(OUTPUT_DIR, '6_3_按日期统计.csv'), index=False, encoding='utf-8-sig')
    channel_stats.to_csv(os.path.join(OUTPUT_DIR, '6_4_按订餐渠道统计.csv'), index=False, encoding='utf-8-sig')
    refund_violation.to_csv(os.path.join(OUTPUT_DIR, '6_5_退餐原因与忌口关联.csv'), index=False, encoding='utf-8-sig')

    elderly_with_restriction = restrictions[restrictions['忌口类型'] != '无特殊忌口']
    elders_with_violation = violation_records['老人ID'].nunique()

    canteen_replace_violations = violation_records[violation_records['订单来源'] == '食堂替换餐品']

    summary = {
        '分析项目': '忌口匹配分析',
        '高糖阈值(g)': SUGAR_THRESHOLD_HIGH,
        '高盐阈值(mg)': SODIUM_THRESHOLD_HIGH,
        '高脂阈值(g)': FAT_THRESHOLD_HIGH,
        '有忌口老人数': len(elderly_with_restriction),
        '忌口违规订单总数': len(violation_records),
        '涉及违规老人数': elders_with_violation,
        '高糖违规数': int(violation_records['忌口违规类型'].str.contains('高糖').sum()),
        '高盐违规数': int(violation_records['忌口违规类型'].str.contains('高盐').sum()),
        '高脂违规数': int(violation_records['忌口违规类型'].str.contains('高脂').sum()),
        '老人主动选择违规数': int((violation_records['订单来源'] == '老人主动选择').sum()),
        '家属代订违规数': int((violation_records['订单来源'] == '家属代订').sum()),
        '食堂替换餐品违规数': int((violation_records['订单来源'] == '食堂替换餐品').sum()),
        '食堂替换涉及餐品数': canteen_replace_violations['餐品名称'].nunique() if len(canteen_replace_violations) > 0 else 0,
        '涉及食堂数': violation_records['所属食堂'].nunique(),
        '违规最高食堂': canteen_stats.iloc[0]['所属食堂'] if len(canteen_stats) > 0 else '无',
        '有退餐记录的违规数': int(has_refund_mask.sum()),
    }

    return summary, violation_detail, source_stats, canteen_stats, date_stats, channel_stats


def main():
    print("=" * 60)
    print("分析6：忌口匹配分析")
    print("=" * 60)

    profiles, meals, orders, pickup = load_data()
    summary, detail, source_stats, canteen_stats, date_stats, channel_stats = analyze_dietary_restriction(
        profiles, meals, orders, pickup
    )

    print(f"\n【阈值设置】高糖≥{summary['高糖阈值(g)']}g  高盐≥{summary['高盐阈值(mg)']}mg  高脂≥{summary['高脂阈值(g)']}g")
    print(f"【有忌口老人】{summary['有忌口老人数']}人")
    print(f"【忌口违规订单】总计 {summary['忌口违规订单总数']} 单，涉及 {summary['涉及违规老人数']} 位老人")
    print(f"  - 高糖违规: {summary['高糖违规数']}单")
    print(f"  - 高盐违规: {summary['高盐违规数']}单")
    print(f"  - 高脂违规: {summary['高脂违规数']}单")
    print(f"\n【按订单来源区分】")
    print(f"  - 老人主动选择: {summary['老人主动选择违规数']}单")
    print(f"  - 家属代订: {summary['家属代订违规数']}单")
    print(f"  - 食堂替换餐品: {summary['食堂替换餐品违规数']}单 (涉及{summary['食堂替换涉及餐品数']}种餐品)")
    print(f"\n【统计范围】涉及 {summary['涉及食堂数']} 个食堂，违规最高: {summary['违规最高食堂']}")
    print(f"【退餐关联】有退餐记录的违规订单: {summary['有退餐记录的违规数']}单")
    print(f"\n明细清单已保存: output/6_忌口匹配分析明细.csv")
    print(f"统计报表已保存: output/6_1_按订单来源统计.csv 等5个统计文件")

    return summary, detail


if __name__ == '__main__':
    main()
