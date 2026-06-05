import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

np.random.seed(42)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
os.makedirs(DATA_DIR, exist_ok=True)

COMMUNITIES = ['朝阳社区', '海淀社区', '西城社区', '东城社区', '丰台社区', '石景山社区']
CANTEENS = {
    '朝阳社区': '朝阳幸福食堂', '海淀社区': '海淀康乐食堂',
    '西城社区': '西城长者食堂', '东城社区': '东城温馨食堂',
    '丰台社区': '丰台惠民食堂', '石景山社区': '石景山爱心食堂',
}
CHRONIC_DISEASES = ['无', '糖尿病', '高血压', '糖尿病+高血压']
SUBSIDY_TYPES = ['A类(特困)', 'B类(低保)', 'C类(低收入)', 'D类(普通)']
SUBSIDY_AMOUNTS = {'A类(特困)': 600, 'B类(低保)': 400, 'C类(低收入)': 200, 'D类(普通)': 100}
PICKUP_METHODS = ['堂食', '配送', '自提']
MEAL_TIMES = ['早餐', '午餐', '晚餐']
VERIFY_METHODS = ['人脸识别', '刷卡', '手工核销']
ROUTES = [f'R{str(i).zfill(3)}' for i in range(1, 16)]
DELIVERY_STAFF = [f'配送员{str(i).zfill(2)}' for i in range(1, 11)]

END_DATE = datetime(2026, 5, 31)
START_DATE = datetime(2025, 12, 1)
TOTAL_DAYS = (END_DATE - START_DATE).days

N_ELDERS = 300
N_ORDERS = 5000
N_SURVEYS = 800


def generate_elderly_profiles():
    eids = [f'E{str(i).zfill(4)}' for i in range(1, N_ELDERS + 1)]
    ages = np.clip(np.random.normal(75, 7, N_ELDERS), 60, 95).astype(int)
    communities = np.random.choice(COMMUNITIES, N_ELDERS)
    chronics = np.random.choice(CHRONIC_DISEASES, N_ELDERS, p=[0.35, 0.20, 0.25, 0.20])
    genders = np.random.choice(['男', '女'], N_ELDERS)
    building_nos = np.random.randint(1, 30, N_ELDERS)
    unit_nos = np.random.randint(1, 6, N_ELDERS)
    room_nos = np.random.randint(101, 605, N_ELDERS)
    addresses = [f'{c}{b}号楼{u}单元{r}号' for c, b, u, r in zip(communities, building_nos, unit_nos, room_nos)]
    prefixes = np.random.choice(['3', '5', '7', '8', '9'], N_ELDERS)
    suffixes = np.random.randint(100000000, 999999999, N_ELDERS)
    phones = [f'1{p}{s}' for p, s in zip(prefixes, suffixes)]
    surnames = np.random.choice(['张', '王', '李', '赵', '刘'], N_ELDERS)
    contacts = [f'紧急联系人{s}' for s in surnames]

    return pd.DataFrame({
        '老人ID': eids, '姓名': [f'老人{e}' for e in eids],
        '性别': genders, '年龄': ages, '所属社区': communities,
        '住址': addresses, '联系电话': phones, '慢病标签': chronics, '紧急联系人': contacts,
    })


def generate_subsidy_levels(profiles):
    n = len(profiles)
    stypes = []
    for c in profiles['慢病标签']:
        if c == '无':
            stypes.append(np.random.choice(SUBSIDY_TYPES, p=[0.02, 0.08, 0.30, 0.60]))
        elif c == '糖尿病+高血压':
            stypes.append(np.random.choice(SUBSIDY_TYPES, p=[0.15, 0.35, 0.35, 0.15]))
        else:
            stypes.append(np.random.choice(SUBSIDY_TYPES, p=[0.08, 0.22, 0.40, 0.30]))
    amounts = [SUBSIDY_AMOUNTS[s] for s in stypes]
    start_offsets = np.random.randint(30, 365, n)
    end_offsets = np.random.randint(30, 180, n)
    starts = [(START_DATE - timedelta(days=int(d))).strftime('%Y-%m-%d') for d in start_offsets]
    ends = [(END_DATE + timedelta(days=int(d))).strftime('%Y-%m-%d') for d in end_offsets]

    return pd.DataFrame({
        '老人ID': profiles['老人ID'], '补贴类型': stypes,
        '月补贴金额': amounts, '生效起始日': starts,
        '生效截止日': ends, '状态': ['生效'] * n,
    })


def generate_pickup_methods(profiles):
    n = len(profiles)
    methods = []
    for age in profiles['年龄']:
        if age >= 80:
            methods.append(np.random.choice(PICKUP_METHODS, p=[0.30, 0.55, 0.15]))
        else:
            methods.append(np.random.choice(PICKUP_METHODS, p=[0.45, 0.35, 0.20]))
    canteens = [CANTEENS[c] for c in profiles['所属社区']]
    return pd.DataFrame({'老人ID': profiles['老人ID'], '取餐方式': methods, '默认取餐点': canteens})


def generate_meal_nutrition():
    return pd.DataFrame([
        ('M001', '红烧肉套餐', 650, 55, 1200, 8, False, False),
        ('M002', '清蒸鱼套餐', 420, 30, 600, 3, True, True),
        ('M003', '西红柿鸡蛋面', 380, 48, 800, 6, False, True),
        ('M004', '宫保鸡丁套餐', 520, 42, 950, 7, False, False),
        ('M005', '小米粥+馒头+咸菜', 320, 58, 1500, 4, False, False),
        ('M006', '蒸南瓜+杂粮粥', 280, 45, 300, 5, True, True),
        ('M007', '糖醋排骨套餐', 620, 52, 1050, 15, False, False),
        ('M008', '冬瓜排骨汤套餐', 400, 35, 700, 4, True, True),
        ('M009', '蛋炒饭', 480, 60, 900, 5, False, False),
        ('M010', '白菜豆腐煲', 300, 25, 500, 3, True, True),
        ('M011', '红烧狮子头套餐', 580, 40, 1100, 6, False, False),
        ('M012', '蒸蛋羹+蔬菜+米饭', 350, 42, 650, 3, True, True),
        ('M013', '咖喱牛肉饭', 550, 50, 1000, 4, False, False),
        ('M014', '皮蛋瘦肉粥+花卷', 340, 46, 850, 3, False, True),
        ('M015', '糖醋里脊套餐', 560, 48, 1050, 14, False, False),
        ('M016', '清炒时蔬+米饭', 280, 38, 400, 2, True, True),
        ('M017', '炸酱面', 450, 55, 1200, 6, False, False),
        ('M018', '南瓜粥+全麦面包', 260, 40, 350, 5, True, True),
        ('M019', '鱼香肉丝套餐', 500, 44, 980, 8, False, False),
        ('M020', '素三鲜包子+豆浆', 300, 38, 450, 3, True, True),
        ('M021', '酱肘子套餐', 680, 38, 1400, 5, False, False),
        ('M022', '紫薯粥+鸡蛋', 250, 35, 300, 4, True, True),
        ('M023', '回锅肉套餐', 600, 42, 1150, 7, False, False),
        ('M024', '银耳莲子羹+馒头', 270, 50, 350, 10, False, True),
        ('M025', '蒜蓉西兰花+米饭', 290, 35, 450, 2, True, True),
        ('M026', '蜜汁叉烧饭', 550, 48, 980, 18, False, False),
        ('M027', '山药排骨汤+米饭', 380, 40, 650, 3, True, True),
        ('M028', '酸辣粉', 400, 52, 1300, 5, False, False),
        ('M029', '荞麦面+蔬菜沙拉', 310, 35, 380, 2, True, True),
        ('M030', '红豆沙+油条', 350, 55, 550, 12, False, False),
    ], columns=['餐品ID', '餐品名称', '热量(kcal)', '碳水(g)', '钠(mg)', '糖(g)', '低盐标识', '低糖标识'])


def generate_orders(profiles, subsidy_levels, pickup_methods, meals):
    inactive_eids = set(profiles.sample(n=40, random_state=42)['老人ID'].tolist())
    active_eids = [eid for eid in profiles['老人ID'].tolist() if eid not in inactive_eids]

    is_inactive = np.random.random(N_ORDERS) < 0.08
    elder_pool = np.array(active_eids)
    inactive_pool = np.array(list(inactive_eids))

    eids = np.where(is_inactive, np.random.choice(inactive_pool, N_ORDERS), np.random.choice(elder_pool, N_ORDERS))

    day_offsets = np.where(is_inactive, np.random.randint(0, 30, N_ORDERS), np.random.randint(0, TOTAL_DAYS, N_ORDERS))

    meal_ids = np.random.choice(meals['餐品ID'].values, N_ORDERS)
    meal_times = np.random.choice(MEAL_TIMES, N_ORDERS, p=[0.20, 0.50, 0.30])

    order_dates = pd.to_datetime(START_DATE) + pd.to_timedelta(day_offsets, unit='D')
    order_date_strs = order_dates.strftime('%Y-%m-%d')

    subsidy_map = dict(zip(subsidy_levels['老人ID'], subsidy_levels['月补贴金额']))
    subsidy_amts = np.array([subsidy_map.get(eid, 0) for eid in eids], dtype=float)

    prices = np.random.choice([8, 10, 12, 15], N_ORDERS)
    covers = np.minimum(subsidy_amts / 30, prices).round(1)
    self_pays = (prices - covers).round(1)

    oids = [f'O{str(i).zfill(6)}' for i in range(1, N_ORDERS + 1)]

    return pd.DataFrame({
        '订单ID': oids, '老人ID': eids, '餐品ID': meal_ids,
        '下单日期': order_date_strs, '餐次': meal_times,
        '餐品单价': prices, '补贴抵扣': covers, '自付金额': self_pays,
    })


def generate_delivery_times(orders, pickup_methods):
    delivery_orders = orders.merge(pickup_methods[['老人ID', '取餐方式']], on='老人ID', how='left')
    delivery_orders = delivery_orders[delivery_orders['取餐方式'] == '配送'].reset_index(drop=True)
    n = len(delivery_orders)

    routes = np.random.choice(ROUTES, n)
    staffs = np.random.choice(DELIVERY_STAFF, n)

    depart_hours = np.where(delivery_orders['餐次'] == '早餐', 6,
                   np.where(delivery_orders['餐次'] == '午餐', 10, 16))
    promise_hours = np.where(delivery_orders['餐次'] == '早餐', 8,
                    np.where(delivery_orders['餐次'] == '午餐', 12, 18))

    depart_minutes = np.random.randint(0, 30, n)
    order_dates = pd.to_datetime(delivery_orders['下单日期'])
    depart_times = order_dates + pd.to_timedelta(depart_hours * 60 + depart_minutes, unit='m')

    slow_mask = np.isin(routes, ['R003', 'R007', 'R012'])
    delay_fast = np.where(np.random.random(n) < 0.75,
                          np.random.randint(-10, 20, n),
                          np.random.randint(20, 45, n))
    delay_slow = np.where(np.random.random(n) < 0.40,
                          np.random.randint(0, 20, n),
                          np.random.randint(30, 90, n))
    delays = np.where(slow_mask, delay_slow, delay_fast)

    arrive_times = depart_times + pd.to_timedelta(30 + delays, unit='m')
    promise_times = depart_times + pd.to_timedelta(45, unit='m')

    dids = [f'D{str(i).zfill(6)}' for i in range(1, n + 1)]

    return pd.DataFrame({
        '配送ID': dids, '订单ID': delivery_orders['订单ID'].values,
        '配送员': staffs, '路线编号': routes,
        '出发时间': depart_times.dt.strftime('%Y-%m-%d %H:%M'),
        '送达时间': arrive_times.dt.strftime('%Y-%m-%d %H:%M'),
        '承诺送达时间': promise_times.dt.strftime('%Y-%m-%d %H:%M'),
    })


def generate_verification_vouchers(orders, pickup_methods):
    suspicious_eids = set(orders['老人ID'].sample(n=15, random_state=100).tolist())
    n = len(orders)

    pm_map = dict(zip(pickup_methods['老人ID'], pickup_methods['取餐方式']))

    verify_hours = np.where(orders['餐次'] == '早餐', np.random.randint(6, 9, n),
                   np.where(orders['餐次'] == '午餐', np.random.randint(11, 14, n),
                            np.random.randint(17, 20, n)))
    verify_minutes = np.random.randint(0, 59, n)
    order_dates = pd.to_datetime(orders['下单日期'])
    verify_times = order_dates + pd.to_timedelta(verify_hours * 60 + verify_minutes, unit='m')

    vmethods = np.random.choice(VERIFY_METHODS, n, p=[0.60, 0.30, 0.10])

    for i in range(n):
        eid = orders.iloc[i]['老人ID']
        if eid in suspicious_eids:
            r = np.random.random()
            if r < 0.35:
                vmethods[i] = '手工核销'
            elif r < 0.65:
                verify_times.iloc[i] += pd.Timedelta(hours=np.random.randint(2, 6))
                vmethods[i] = '刷卡'
            else:
                vmethods[i] = np.random.choice(VERIFY_METHODS, p=[0.50, 0.30, 0.20])

    operators = np.where(vmethods == '手工核销',
                         [f'操作员{np.random.randint(1, 6)}' for _ in range(n)],
                         '系统')

    vids = [f'V{str(i).zfill(6)}' for i in range(1, n + 1)]

    return pd.DataFrame({
        '核销ID': vids, '订单ID': orders['订单ID'].values,
        '老人ID': orders['老人ID'].values,
        '核销时间': verify_times.dt.strftime('%Y-%m-%d %H:%M'),
        '核销方式': vmethods, '操作人': operators,
    })


def generate_satisfaction_surveys(profiles, orders):
    decline_canteens = {'丰台惠民食堂', '石景山爱心食堂'}
    community_canteen = {c: CANTEENS[c] for c in COMMUNITIES}
    eid_community = dict(zip(profiles['老人ID'], profiles['所属社区']))

    surveyed = orders.sample(n=min(N_SURVEYS, len(orders)), random_state=200).reset_index(drop=True)
    n = len(surveyed)

    eids = surveyed['老人ID'].values
    canteens = np.array([community_canteen.get(eid_community.get(eid, ''), '') for eid in eids])

    order_dates = pd.to_datetime(surveyed['下单日期'])
    survey_dates = order_dates + pd.to_timedelta(np.random.randint(1, 7, n), unit='D')
    month_offsets = (survey_dates.dt.year - START_DATE.year) * 12 + (survey_dates.dt.month - START_DATE.month)

    is_decline = np.isin(canteens, list(decline_canteens)) & (month_offsets > 3)
    scores = np.where(is_decline,
                      np.clip(np.random.normal(2.2, 0.8, n), 1, 5).astype(int),
                      np.clip(np.random.normal(3.8, 0.7, n), 1, 5).astype(int))

    opinion_map = {1: '饭菜质量差，不卫生', 2: '送餐太慢，经常凉了', 3: '味道一般', 4: '基本满意', 5: '很好，感谢政府'}
    opinions = np.where(np.random.random(n) < 0.5,
                        [opinion_map.get(int(s), '') for s in scores], '')

    sids = [f'S{str(i).zfill(6)}' for i in range(1, n + 1)]

    return pd.DataFrame({
        '回访ID': sids, '老人ID': eids, '社区食堂': canteens,
        '评分': scores, '回访日期': survey_dates.dt.strftime('%Y-%m-%d'),
        '意见内容': opinions,
    })


def main():
    print("=== 开始生成模拟数据 ===")

    print("1/8 生成老人档案...")
    profiles = generate_elderly_profiles()
    profiles.to_csv(os.path.join(DATA_DIR, 'elderly_profiles.csv'), index=False, encoding='utf-8-sig')
    print(f"   老人档案: {len(profiles)} 条")

    print("2/8 生成补贴等级...")
    subsidy = generate_subsidy_levels(profiles)
    subsidy.to_csv(os.path.join(DATA_DIR, 'subsidy_levels.csv'), index=False, encoding='utf-8-sig')
    print(f"   补贴等级: {len(subsidy)} 条")

    print("3/8 生成取餐方式...")
    pickup = generate_pickup_methods(profiles)
    pickup.to_csv(os.path.join(DATA_DIR, 'pickup_methods.csv'), index=False, encoding='utf-8-sig')
    print(f"   取餐方式: {len(pickup)} 条")

    print("4/8 生成餐品营养...")
    meals = generate_meal_nutrition()
    meals.to_csv(os.path.join(DATA_DIR, 'meal_nutrition.csv'), index=False, encoding='utf-8-sig')
    print(f"   餐品营养: {len(meals)} 条")

    print("5/8 生成订餐记录...")
    orders = generate_orders(profiles, subsidy, pickup, meals)
    orders.to_csv(os.path.join(DATA_DIR, 'order_records.csv'), index=False, encoding='utf-8-sig')
    print(f"   订餐记录: {len(orders)} 条")

    print("6/8 生成配送时间...")
    delivery = generate_delivery_times(orders, pickup)
    delivery.to_csv(os.path.join(DATA_DIR, 'delivery_times.csv'), index=False, encoding='utf-8-sig')
    print(f"   配送时间: {len(delivery)} 条")

    print("7/8 生成核销凭证...")
    verify = generate_verification_vouchers(orders, pickup)
    verify.to_csv(os.path.join(DATA_DIR, 'verification_vouchers.csv'), index=False, encoding='utf-8-sig')
    print(f"   核销凭证: {len(verify)} 条")

    print("8/8 生成满意回访...")
    surveys = generate_satisfaction_surveys(profiles, orders)
    surveys.to_csv(os.path.join(DATA_DIR, 'satisfaction_surveys.csv'), index=False, encoding='utf-8-sig')
    print(f"   满意回访: {len(surveys)} 条")

    print("\n=== 模拟数据生成完成，文件保存在 data/ 目录 ===")


if __name__ == '__main__':
    main()
