import os
import sys
import argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scripts.generate_data import main as generate_data
from scripts.analysis_subsidy import main as analysis_subsidy
from scripts.analysis_meal import main as analysis_meal
from scripts.analysis_delivery import main as analysis_delivery
from scripts.analysis_verify import main as analysis_verify
from scripts.analysis_satisfaction import main as analysis_satisfaction

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')

REQUIRED_CSV = [
    'elderly_profiles.csv', 'subsidy_levels.csv', 'pickup_methods.csv',
    'meal_nutrition.csv', 'order_records.csv', 'delivery_times.csv',
    'verification_vouchers.csv', 'satisfaction_surveys.csv',
]


def check_data_ready():
    if not os.path.isdir(DATA_DIR):
        return False
    return all(os.path.isfile(os.path.join(DATA_DIR, f)) for f in REQUIRED_CSV)


def run_analysis():
    start = datetime.now()
    print("╔" + "═" * 58 + "╗")
    print("║" + "老人助餐补贴数据分析系统".center(48) + "║")
    print("║" + f"运行时间: {start.strftime('%Y-%m-%d %H:%M:%S')}".center(48) + "║")
    print("╚" + "═" * 58 + "╝")

    print("\n" + "▶" * 20 + " 执行数据分析 " + "▶" * 20)
    print(f"数据目录: {os.path.abspath(DATA_DIR)}")

    summaries = []

    print()
    s1, _ = analysis_subsidy()
    summaries.append(('1. 长期未使用补贴老人筛查', s1))

    print()
    s2, _ = analysis_meal()
    summaries.append(('2. 餐品与慢病适配风险分析', s2))

    print()
    s3, _ = analysis_delivery()
    summaries.append(('3. 配送路线超时分析', s3))

    print()
    s4, _ = analysis_verify()
    summaries.append(('4. 核销记录冒领代领疑似筛查', s4))

    print()
    s5, _ = analysis_satisfaction()
    summaries.append(('5. 社区食堂满意度下降趋势分析', s5))

    end = datetime.now()
    duration = (end - start).total_seconds()

    print("\n" + "╔" + "═" * 58 + "╗")
    print("║" + "分析汇总报告".center(48) + "║")
    print("╠" + "═" * 58 + "╣")

    for title, summary in summaries:
        print(f"║ 【{title}】")
        for k, v in summary.items():
            if k == '分析项目':
                continue
            print(f"║   {k}: {v}")
        print("║")

    print("╠" + "═" * 58 + "╣")
    print(f"║ 总耗时: {duration:.1f}秒")
    print(f"║ 结果目录: {os.path.abspath(OUTPUT_DIR)}")
    print("╠" + "═" * 58 + "╣")
    print("║ 输出文件清单:")
    output_files = sorted(os.listdir(OUTPUT_DIR))
    for f in output_files:
        fpath = os.path.join(OUTPUT_DIR, f)
        size = os.path.getsize(fpath)
        print(f"║   {f} ({size:,} bytes)")
    print("╚" + "═" * 58 + "╝")

    print(f"\n✅ 全部分析完成，耗时 {duration:.1f} 秒")
    print(f"📁 详细结果请查看: {os.path.abspath(OUTPUT_DIR)}")
    print("📋 每份CSV均可追溯至原始记录，供民政窗口复核使用")


def main():
    parser = argparse.ArgumentParser(description='老人助餐补贴数据分析系统')
    parser.add_argument('--generate', action='store_true',
                        help='生成模拟数据到 data/ 目录（会覆盖已有CSV）')
    parser.add_argument('--force-generate', action='store_true',
                        help='强制重新生成模拟数据，即使 data/ 已有文件')
    args = parser.parse_args()

    if args.generate or args.force_generate:
        if check_data_ready() and not args.force_generate:
            print("⚠️  data/ 目录已包含业务数据，使用 --force-generate 强制覆盖")
            print("   普通复跑将直接读取现有数据，不会覆盖。")
            sys.exit(1)
        print("=" * 60)
        print("生成模拟数据（--generate 模式）")
        print("=" * 60)
        os.environ['FORCE_GENERATE'] = '1'
        generate_data()
        print()
        print("模拟数据已生成，现在执行分析...")
        print()

    if not check_data_ready():
        print("❌ data/ 目录缺少必要的CSV文件，请先运行:")
        print("   python run_all.py --generate")
        print("   或将真实业务数据放入 data/ 目录")
        sys.exit(1)

    run_analysis()


if __name__ == '__main__':
    main()
