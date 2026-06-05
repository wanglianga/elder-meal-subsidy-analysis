import os
import pandas as pd
from datetime import datetime, timedelta

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

INACTIVE_DAYS = 90


def load_data():
    profiles = pd.read_csv(os.path.join(DATA_DIR, 'elderly_profiles.csv'), encoding='utf-8-sig')
    subsidy = pd.read_csv(os.path.join(DATA_DIR, 'subsidy_levels.csv'), encoding='utf-8-sig')
    orders = pd.read_csv(os.path.join(DATA_DIR, 'order_records.csv'), encoding='utf-8-sig')
    pickup = pd.read_csv(os.path.join(DATA_DIR, 'pickup_methods.csv'), encoding='utf-8-sig')
    return profiles, subsidy, orders, pickup


def analyze_inactive_subsidy(profiles, subsidy, orders, pickup):
    cutoff_date = (datetime(2026, 5, 31) - timedelta(days=INACTIVE_DAYS)).strftime('%Y-%m-%d')
    active_subsidy = subsidy[subsidy['状态'] == '生效'].copy()

    last_orders = orders.groupby('老人ID').agg(
        最近下单日期=('下单日期', 'max'),
        累计下单次数=('订单ID', 'count'),
        累计补贴抵扣=('补贴抵扣', 'sum')
    ).reset_index()

    merged = active_subsidy.merge(profiles[['老人ID', '姓名', '性别', '年龄', '所属社区', '慢病标签']], on='老人ID', how='left')
    merged = merged.merge(pickup[['老人ID', '取餐方式', '默认取餐点']], on='老人ID', how='left')
    merged = merged.merge(last_orders, on='老人ID', how='left')

    merged['最近下单日期'] = merged['最近下单日期'].fillna('从未下单')
    merged['累计下单次数'] = merged['累计下单次数'].fillna(0).astype(int)
    merged['累计补贴抵扣'] = merged['累计补贴抵扣'].fillna(0)

    inactive = merged[
        (merged['最近下单日期'] < cutoff_date) | (merged['最近下单日期'] == '从未下单')
    ].copy()

    inactive['未使用天数'] = inactive['最近下单日期'].apply(
        lambda x: (datetime(2026, 5, 31) - datetime.strptime(x, '%Y-%m-%d')).days
        if x != '从未下单' else (datetime(2026, 5, 31) - datetime.strptime(merged['生效起始日'].iloc[0] if len(merged) > 0 else '2025-12-01', '%Y-%m-%d')).days
    )

    inactive = inactive.sort_values('未使用天数', ascending=False)

    detail_cols = [
        '老人ID', '姓名', '性别', '年龄', '所属社区', '慢病标签',
        '补贴类型', '月补贴金额', '生效起始日', '生效截止日',
        '取餐方式', '默认取餐点', '最近下单日期', '累计下单次数',
        '累计补贴抵扣', '未使用天数'
    ]
    detail = inactive[detail_cols].copy()

    detail.to_csv(os.path.join(OUTPUT_DIR, '1_长期未使用补贴老人明细.csv'), index=False, encoding='utf-8-sig')

    summary = {
        '分析项目': '长期未使用补贴老人筛查',
        '统计截止日': '2026-05-31',
        '未使用阈值(天)': INACTIVE_DAYS,
        '生效补贴老人总数': len(active_subsidy),
        '长期未使用人数': len(inactive),
        '占比': f"{len(inactive)/len(active_subsidy)*100:.1f}%",
        '从未下单人数': len(inactive[inactive['最近下单日期'] == '从未下单']),
        'A类特困未使用': len(inactive[inactive['补贴类型'] == 'A类(特困)']),
        'B类低保未使用': len(inactive[inactive['补贴类型'] == 'B类(低保)']),
    }

    return summary, detail


def main():
    print("=" * 60)
    print("分析1：长期未使用补贴老人筛查")
    print("=" * 60)

    profiles, subsidy, orders, pickup = load_data()
    summary, detail = analyze_inactive_subsidy(profiles, subsidy, orders, pickup)

    print(f"\n【统计截止日】{summary['统计截止日']}")
    print(f"【未使用阈值】{summary['未使用阈值(天)']}天")
    print(f"【生效补贴老人总数】{summary['生效补贴老人总数']}")
    print(f"【长期未使用人数】{summary['长期未使用人数']}（{summary['占比']}）")
    print(f"【其中从未下单】{summary['从未下单人数']}")
    print(f"【A类特困未使用】{summary['A类特困未使用']}")
    print(f"【B类低保未使用】{summary['B类低保未使用']}")
    print(f"\n明细清单已保存: output/1_长期未使用补贴老人明细.csv")

    return summary, detail


if __name__ == '__main__':
    main()
