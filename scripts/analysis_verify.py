import os
import pandas as pd
from datetime import datetime, timedelta

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

SAME_ELDER_GAP_MINUTES = 120


def load_data():
    profiles = pd.read_csv(os.path.join(DATA_DIR, 'elderly_profiles.csv'), encoding='utf-8-sig')
    orders = pd.read_csv(os.path.join(DATA_DIR, 'order_records.csv'), encoding='utf-8-sig')
    verify = pd.read_csv(os.path.join(DATA_DIR, 'verification_vouchers.csv'), encoding='utf-8-sig')
    pickup = pd.read_csv(os.path.join(DATA_DIR, 'pickup_methods.csv'), encoding='utf-8-sig')
    return profiles, orders, verify, pickup


def analyze_verification_fraud(profiles, orders, verify, pickup):
    verify['核销时间_dt'] = pd.to_datetime(verify['核销时间'])
    verify = verify.sort_values(['老人ID', '核销时间_dt'])

    suspicious_records = []

    pattern1 = verify.merge(pickup[['老人ID', '取餐方式']], on='老人ID', how='left')
    manual_anomaly = pattern1[
        (pattern1['取餐方式'] != '配送') &
        (pattern1['核销方式'] == '手工核销')
    ].copy()
    manual_anomaly['异常类型'] = '堂食/自提却手工核销'
    manual_anomaly['异常说明'] = manual_anomaly.apply(
        lambda r: f"取餐方式为{r['取餐方式']}，但采用手工核销，操作人: {r['操作人']}", axis=1
    )
    suspicious_records.append(manual_anomaly)

    verify_sorted = verify.sort_values(['老人ID', '核销时间_dt']).copy()
    verify_sorted['前次核销时间'] = verify_sorted.groupby('老人ID')['核销时间_dt'].shift(1)
    verify_sorted['前次核销方式'] = verify_sorted.groupby('老人ID')['核销方式'].shift(1)
    verify_sorted['前次核销ID'] = verify_sorted.groupby('老人ID')['核销ID'].shift(1)
    verify_sorted['间隔分钟'] = (
        verify_sorted['核销时间_dt'] - verify_sorted['前次核销时间']
    ).dt.total_seconds() / 60

    rapid_verify = verify_sorted[
        (verify_sorted['间隔分钟'] > 0) &
        (verify_sorted['间隔分钟'] < SAME_ELDER_GAP_MINUTES)
    ].copy()
    rapid_verify['异常类型'] = '同一老人短时间多次核销'
    rapid_verify['异常说明'] = rapid_verify.apply(
        lambda r: f"与核销{r['前次核销ID']}间隔仅{r['间隔分钟']:.0f}分钟", axis=1
    )
    suspicious_records.append(rapid_verify)

    verify_sorted['前次核销失败'] = verify_sorted['前次核销方式'].apply(
        lambda x: True if pd.notna(x) and '手工' in str(x) else False
    )
    fail_retry = verify_sorted[
        (verify_sorted['前次核销失败'] == True) &
        (verify_sorted['核销方式'] != '人脸识别')
    ].copy()
    fail_retry['异常类型'] = '非人脸核销后继续非人脸'
    fail_retry['异常说明'] = fail_retry.apply(
        lambda r: f"前次{r['前次核销方式']}核销，本次{r['核销方式']}核销，均非人脸验证", axis=1
    )
    suspicious_records.append(fail_retry)

    all_suspicious = pd.concat(suspicious_records, ignore_index=True)
    all_suspicious = all_suspicious.drop_duplicates(subset=['核销ID', '异常类型'])

    all_suspicious = all_suspicious.merge(
        orders[['订单ID', '餐品ID', '下单日期', '餐次']], on='订单ID', how='left'
    )
    all_suspicious = all_suspicious.merge(
        profiles[['老人ID', '姓名', '年龄', '所属社区']], on='老人ID', how='left'
    )

    detail_cols = [
        '核销ID', '订单ID', '老人ID', '姓名', '年龄', '所属社区',
        '核销时间', '核销方式', '操作人', '异常类型', '异常说明',
        '下单日期', '餐次'
    ]
    available_cols = [c for c in detail_cols if c in all_suspicious.columns]
    detail = all_suspicious[available_cols].sort_values(['异常类型', '老人ID'])

    detail.to_csv(os.path.join(OUTPUT_DIR, '4_核销异常明细.csv'), index=False, encoding='utf-8-sig')

    type_counts = detail['异常类型'].value_counts().to_dict()
    elder_counts = detail.groupby('异常类型')['老人ID'].nunique().to_dict()

    summary = {
        '分析项目': '核销记录冒领代领疑似筛查',
        '短时间重核阈值(分钟)': SAME_ELDER_GAP_MINUTES,
        '核销记录总数': len(verify),
        '疑似异常记录数': len(detail),
        '涉及老人数': detail['老人ID'].nunique(),
        '堂食手工核销次数': type_counts.get('堂食/自提却手工核销', 0),
        '短时间多次核销次数': type_counts.get('同一老人短时间多次核销', 0),
        '非人脸连续核销次数': type_counts.get('非人脸核销后继续非人脸', 0),
    }

    return summary, detail


def main():
    print("=" * 60)
    print("分析4：核销记录冒领代领疑似筛查")
    print("=" * 60)

    profiles, orders, verify, pickup = load_data()
    summary, detail = analyze_verification_fraud(profiles, orders, verify, pickup)

    print(f"\n【核销记录总数】{summary['核销记录总数']}")
    print(f"【疑似异常记录】{summary['疑似异常记录数']}条，涉及{summary['涉及老人数']}位老人")
    print(f"【堂食/自提却手工核销】{summary['堂食手工核销次数']}次")
    print(f"【短时间多次核销】{summary['短时间多次核销次数']}次")
    print(f"【非人脸连续核销】{summary['非人脸连续核销次数']}次")
    print(f"\n明细清单已保存: output/4_核销异常明细.csv")

    return summary, detail


if __name__ == '__main__':
    main()
