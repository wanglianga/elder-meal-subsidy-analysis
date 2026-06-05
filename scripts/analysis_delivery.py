import os
import pandas as pd
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

OVERTIME_THRESHOLD_MINUTES = 15


def load_data():
    profiles = pd.read_csv(os.path.join(DATA_DIR, 'elderly_profiles.csv'), encoding='utf-8-sig')
    orders = pd.read_csv(os.path.join(DATA_DIR, 'order_records.csv'), encoding='utf-8-sig')
    delivery = pd.read_csv(os.path.join(DATA_DIR, 'delivery_times.csv'), encoding='utf-8-sig')
    return profiles, orders, delivery


def analyze_delivery_overtime(profiles, orders, delivery):
    delivery['送达时间_dt'] = pd.to_datetime(delivery['送达时间'])
    delivery['承诺送达时间_dt'] = pd.to_datetime(delivery['承诺送达时间'])
    delivery['超时分钟'] = (delivery['送达时间_dt'] - delivery['承诺送达时间_dt']).dt.total_seconds() / 60
    delivery['是否超时'] = delivery['超时分钟'] > OVERTIME_THRESHOLD_MINUTES

    route_stats = delivery.groupby('路线编号').agg(
        配送总次数=('配送ID', 'count'),
        超时次数=('是否超时', 'sum'),
        平均超时分钟=('超时分钟', 'mean'),
        最大超时分钟=('超时分钟', 'max'),
        涉及配送员数=('配送员', 'nunique'),
    ).reset_index()
    route_stats['超时率'] = (route_stats['超时次数'] / route_stats['配送总次数'] * 100).round(1)
    route_stats['超时次数'] = route_stats['超时次数'].astype(int)
    route_stats = route_stats.sort_values('超时率', ascending=False)

    overtime_detail = delivery[delivery['是否超时']].copy()
    overtime_detail = overtime_detail.merge(
        orders[['订单ID', '老人ID', '餐次', '下单日期']], on='订单ID', how='left'
    )
    overtime_detail = overtime_detail.merge(
        profiles[['老人ID', '姓名', '年龄', '所属社区']], on='老人ID', how='left'
    )

    overtime_detail['超时分钟'] = overtime_detail['超时分钟'].round(1)

    detail_cols = [
        '配送ID', '订单ID', '老人ID', '姓名', '年龄', '所属社区',
        '路线编号', '配送员', '出发时间', '送达时间', '承诺送达时间',
        '超时分钟', '餐次'
    ]
    detail_output = overtime_detail[detail_cols].sort_values('超时分钟', ascending=False)
    detail_output.to_csv(os.path.join(OUTPUT_DIR, '3_配送超时明细.csv'), index=False, encoding='utf-8-sig')

    route_stats.to_csv(os.path.join(OUTPUT_DIR, '3_路线超时统计.csv'), index=False, encoding='utf-8-sig')

    high_overtime_routes = route_stats[route_stats['超时率'] > 30]
    worst_route = route_stats.iloc[0] if len(route_stats) > 0 else None

    summary = {
        '分析项目': '配送路线超时分析',
        '超时阈值(分钟)': OVERTIME_THRESHOLD_MINUTES,
        '配送总次数': len(delivery),
        '超时次数': int(delivery['是否超时'].sum()),
        '整体超时率': f"{delivery['是否超时'].mean()*100:.1f}%",
        '路线数': len(route_stats),
        '超时率>30%路线数': len(high_overtime_routes),
        '最差路线': worst_route['路线编号'] if worst_route is not None else '无',
        '最差路线超时率': f"{worst_route['超时率']}%" if worst_route is not None else '无',
    }

    return summary, detail_output, route_stats


def main():
    print("=" * 60)
    print("分析3：配送路线超时分析")
    print("=" * 60)

    profiles, orders, delivery = load_data()
    summary, detail, route_stats = analyze_delivery_overtime(profiles, orders, delivery)

    print(f"\n【超时阈值】>{summary['超时阈值(分钟)']}分钟")
    print(f"【配送总次数】{summary['配送总次数']}")
    print(f"【超时次数】{summary['超时次数']}（超时率{summary['整体超时率']}）")
    print(f"【超时率>30%路线】{summary['超时率>30%路线数']}条")
    print(f"【最差路线】{summary['最差路线']}（超时率{summary['最差路线超时率']}）")
    print(f"\n明细清单已保存: output/3_配送超时明细.csv")
    print(f"路线统计已保存: output/3_路线超时统计.csv")

    return summary, detail


if __name__ == '__main__':
    main()
