import os
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

SUGAR_THRESHOLD_HIGH = 10
SODIUM_THRESHOLD_HIGH = 1000


def load_data():
    profiles = pd.read_csv(os.path.join(DATA_DIR, 'elderly_profiles.csv'), encoding='utf-8-sig')
    meals = pd.read_csv(os.path.join(DATA_DIR, 'meal_nutrition.csv'), encoding='utf-8-sig')
    orders = pd.read_csv(os.path.join(DATA_DIR, 'order_records.csv'), encoding='utf-8-sig')
    subsidy = pd.read_csv(os.path.join(DATA_DIR, 'subsidy_levels.csv'), encoding='utf-8-sig')
    return profiles, meals, orders, subsidy


def analyze_meal_disease_risk(profiles, meals, orders, subsidy):
    diabetes_elders = profiles[
        profiles['慢病标签'].str.contains('糖尿病')
    ][['老人ID', '姓名', '年龄', '所属社区', '慢病标签']].copy()

    hypertension_elders = profiles[
        profiles['慢病标签'].str.contains('高血压')
    ][['老人ID', '姓名', '年龄', '所属社区', '慢病标签']].copy()

    high_sugar_meals = meals[meals['糖(g)'] >= SUGAR_THRESHOLD_HIGH][
        ['餐品ID', '餐品名称', '热量(kcal)', '碳水(g)', '糖(g)', '低糖标识']
    ].copy()
    high_sugar_meals['风险类型'] = '高糖'

    high_sodium_meals = meals[meals['钠(mg)'] >= SODIUM_THRESHOLD_HIGH][
        ['餐品ID', '餐品名称', '热量(kcal)', '钠(mg)', '低盐标识']
    ].copy()
    high_sodium_meals['风险类型'] = '高钠'

    diabetes_orders = orders.merge(diabetes_elders, on='老人ID', how='inner')
    diabetes_risk = diabetes_orders.merge(high_sugar_meals[['餐品ID', '风险类型', '糖(g)']], on='餐品ID', how='inner')
    diabetes_risk = diabetes_risk.merge(meals[['餐品ID', '餐品名称', '钠(mg)']], on='餐品ID', how='left')
    diabetes_risk['慢病风险'] = '糖尿病+高糖餐品'

    hypertension_orders = orders.merge(hypertension_elders, on='老人ID', how='inner')
    hypertension_risk = hypertension_orders.merge(high_sodium_meals[['餐品ID', '风险类型', '钠(mg)']], on='餐品ID', how='inner')
    hypertension_risk = hypertension_risk.merge(meals[['餐品ID', '餐品名称', '糖(g)']], on='餐品ID', how='left')
    hypertension_risk['慢病风险'] = '高血压+高钠餐品'

    risk_detail_cols = [
        '订单ID', '老人ID', '姓名', '年龄', '所属社区', '慢病标签',
        '餐品ID', '餐品名称', '下单日期', '餐次', '慢病风险', '糖(g)', '钠(mg)'
    ]
    diabetes_detail = diabetes_risk[risk_detail_cols].copy()
    hypertension_detail = hypertension_risk[risk_detail_cols].copy()

    all_risk = pd.concat([diabetes_detail, hypertension_detail], ignore_index=True)
    all_risk = all_risk.sort_values(['慢病风险', '老人ID', '下单日期'])

    all_risk.to_csv(os.path.join(OUTPUT_DIR, '2_餐品慢病风险明细.csv'), index=False, encoding='utf-8-sig')

    diabetes_meal_stats = diabetes_risk.groupby('餐品名称').agg(
        糖尿病老人点餐次数=('订单ID', 'count'),
        平均糖含量=('糖(g)', 'mean')
    ).reset_index().sort_values('糖尿病老人点餐次数', ascending=False)

    hypertension_meal_stats = hypertension_risk.groupby('餐品名称').agg(
        高血压老人点餐次数=('订单ID', 'count'),
        平均钠含量=('钠(mg)', 'mean')
    ).reset_index().sort_values('高血压老人点餐次数', ascending=False)

    summary = {
        '分析项目': '餐品与慢病适配风险分析',
        '高糖阈值(g)': SUGAR_THRESHOLD_HIGH,
        '高钠阈值(mg)': SODIUM_THRESHOLD_HIGH,
        '糖尿病老人人数': len(diabetes_elders),
        '高血压老人人数': len(hypertension_elders),
        '高糖餐品数': len(high_sugar_meals),
        '高钠餐品数': len(high_sodium_meals),
        '糖尿病老人点高糖餐次数': len(diabetes_risk),
        '高血压老人点高钠餐次数': len(hypertension_risk),
        '涉及糖尿病老人数': diabetes_risk['老人ID'].nunique(),
        '涉及高血压老人数': hypertension_risk['老人ID'].nunique(),
        '糖尿病风险最高餐品': diabetes_meal_stats.iloc[0]['餐品名称'] if len(diabetes_meal_stats) > 0 else '无',
        '高血压风险最高餐品': hypertension_meal_stats.iloc[0]['餐品名称'] if len(hypertension_meal_stats) > 0 else '无',
    }

    return summary, all_risk, diabetes_meal_stats, hypertension_meal_stats


def main():
    print("=" * 60)
    print("分析2：餐品与慢病适配风险分析")
    print("=" * 60)

    profiles, meals, orders, subsidy = load_data()
    summary, detail, dm_stats, ht_stats = analyze_meal_disease_risk(profiles, meals, orders, subsidy)

    print(f"\n【高糖阈值】≥{summary['高糖阈值(g)']}g  【高钠阈值】≥{summary['高钠阈值(mg)']}mg")
    print(f"【糖尿病老人】{summary['糖尿病老人人数']}人，点高糖餐{summary['糖尿病老人点高糖餐次数']}次，涉及{summary['涉及糖尿病老人数']}人")
    print(f"【高血压老人】{summary['高血压老人人数']}人，点高钠餐{summary['高血压老人点高钠餐次数']}次，涉及{summary['涉及高血压老人数']}人")
    print(f"【糖尿病风险最高餐品】{summary['糖尿病风险最高餐品']}")
    print(f"【高血压风险最高餐品】{summary['高血压风险最高餐品']}")
    print(f"\n明细清单已保存: output/2_餐品慢病风险明细.csv")

    return summary, detail


if __name__ == '__main__':
    main()
