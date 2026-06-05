import os
import pandas as pd
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

DECLINE_CONSECUTIVE_MONTHS = 2
DECLINE_RATIO_THRESHOLD = -0.3


def load_data():
    surveys = pd.read_csv(os.path.join(DATA_DIR, 'satisfaction_surveys.csv'), encoding='utf-8-sig')
    return surveys


def analyze_satisfaction_decline(surveys):
    surveys['回访日期_dt'] = pd.to_datetime(surveys['回访日期'])
    surveys['月份'] = surveys['回访日期_dt'].dt.to_period('M')

    monthly = surveys.groupby(['社区食堂', '月份']).agg(
        平均评分=('评分', 'mean'),
        回访人数=('回访ID', 'count'),
        评分1分次数=('评分', lambda x: (x == 1).sum()),
        评分2分次数=('评分', lambda x: (x == 2).sum()),
        评分3分次数=('评分', lambda x: (x == 3).sum()),
        评分4分次数=('评分', lambda x: (x == 4).sum()),
        评分5分次数=('评分', lambda x: (x == 5).sum()),
    ).reset_index()
    monthly['平均评分'] = monthly['平均评分'].round(2)

    monthly = monthly.sort_values(['社区食堂', '月份'])
    monthly['上月评分'] = monthly.groupby('社区食堂')['平均评分'].shift(1)
    monthly['环比变化'] = (monthly['平均评分'] - monthly['上月评分']).round(2)

    first_month = monthly.groupby('社区食堂')['月份'].min()
    last_month = monthly.groupby('社区食堂')['月份'].max()
    first_scores = monthly.set_index(['社区食堂', '月份'])['平均评分']

    canteen_stats = monthly.groupby('社区食堂').agg(
        最新月份=('月份', 'last'),
        最新评分=('平均评分', 'last'),
        历史最高评分=('平均评分', 'max'),
        历史最低评分=('平均评分', 'min'),
        总回访次数=('回访人数', 'sum'),
        评分波动幅度=('平均评分', lambda x: round(x.max() - x.min(), 2)),
    ).reset_index()

    decline_canteens = []
    for canteen in monthly['社区食堂'].unique():
        canteen_data = monthly[monthly['社区食堂'] == canteen].sort_values('月份')
        if len(canteen_data) < 3:
            continue

        recent = canteen_data.tail(DECLINE_CONSECUTIVE_MONTHS + 1)
        scores = recent['平均评分'].values
        consecutive_decline = all(
            scores[i] < scores[i - 1] for i in range(1, len(scores))
        )

        first_score = canteen_data.iloc[0]['平均评分']
        last_score = canteen_data.iloc[-1]['平均评分']
        total_change = (last_score - first_score) / first_score if first_score > 0 else 0
        significant_decline = total_change < DECLINE_RATIO_THRESHOLD

        if consecutive_decline or significant_decline:
            decline_canteens.append({
                '社区食堂': canteen,
                '是否连续下降': consecutive_decline,
                '是否显著下降': significant_decline,
                '首月评分': round(first_score, 2),
                '末月评分': round(last_score, 2),
                '累计变化率': f"{total_change*100:.1f}%",
                '连续下降月数': len(scores) - 1 if consecutive_decline else 0,
            })

    decline_df = pd.DataFrame(decline_canteens) if decline_canteens else pd.DataFrame(
        columns=['社区食堂', '是否连续下降', '是否显著下降', '首月评分', '末月评分', '累计变化率', '连续下降月数']
    )

    monthly.to_csv(os.path.join(OUTPUT_DIR, '5_食堂月度满意度趋势.csv'), index=False, encoding='utf-8-sig')
    decline_df.to_csv(os.path.join(OUTPUT_DIR, '5_满意度下降食堂明细.csv'), index=False, encoding='utf-8-sig')

    low_score_detail = surveys[surveys['评分'] <= 2].copy()
    low_score_detail = low_score_detail.merge(
        decline_df[['社区食堂']], on='社区食堂', how='inner'
    ) if len(decline_df) > 0 else low_score_detail.iloc[0:0]
    low_score_detail.to_csv(os.path.join(OUTPUT_DIR, '5_下降食堂差评明细.csv'), index=False, encoding='utf-8-sig')

    summary = {
        '分析项目': '社区食堂满意度下降趋势分析',
        '连续下降判定月数': DECLINE_CONSECUTIVE_MONTHS,
        '显著下降阈值': f"{DECLINE_RATIO_THRESHOLD*100:.0f}%",
        '食堂总数': surveys['社区食堂'].nunique(),
        '满意度下降食堂数': len(decline_df),
        '整体平均评分': round(surveys['评分'].mean(), 2),
    }

    return summary, decline_df, monthly


def main():
    print("=" * 60)
    print("分析5：社区食堂满意度下降趋势分析")
    print("=" * 60)

    surveys = load_data()
    summary, decline_df, monthly = analyze_satisfaction_decline(surveys)

    print(f"\n【食堂总数】{summary['食堂总数']}")
    print(f"【整体平均评分】{summary['整体平均评分']}")
    print(f"【满意度下降食堂数】{summary['满意度下降食堂数']}")
    if len(decline_df) > 0:
        print("\n下降食堂详情：")
        for _, row in decline_df.iterrows():
            print(f"  - {row['社区食堂']}: 首月{row['首月评分']}→末月{row['末月评分']}，累计{row['累计变化率']}")
    print(f"\n月度趋势已保存: output/5_食堂月度满意度趋势.csv")
    print(f"下降食堂明细已保存: output/5_满意度下降食堂明细.csv")
    print(f"差评明细已保存: output/5_下降食堂差评明细.csv")

    return summary, decline_df


if __name__ == '__main__':
    main()
