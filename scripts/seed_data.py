# -*- coding: gbk -*-  
from __future__ import annotations  
  
import asyncio  
import sys  
from datetime import datetime, timedelta, timezone  
from pathlib import Path  
  
from sqlalchemy import delete  
  
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  
  
from app.db.models import Product, ProductPriceSnapshot  
from app.db.session import AsyncSessionLocal, engine  
  
NOW = datetime.now(timezone.utc)  
  
def score(performance, camera=None, battery=None, screen=None, portability=None):  
    data = {'performance': performance, 'battery': battery, 'screen': screen, 'portability': portability}  
    if camera is not None:  
        data['camera'] = camera  
    return {k: v for k, v in data.items() if v is not None}  
  
def p(brand, series, name, category, sub_category, tagline, positioning, guide_price, price_min, price_max, users, scenes, points, bad, scores, features, specs, description, own=False, featured=False, priority=60):  
    return {'brand': brand, 'series': series, 'name': name, 'category': category, 'sub_category': sub_category, 'tagline': tagline, 'positioning': positioning, 'market_status': '在售', 'is_own_brand': own, 'is_featured': featured, 'guide_priority': priority, 'is_active': True, 'guide_price': guide_price, 'price_min': price_min, 'price_max': price_max, 'target_users': users, 'usage_scenarios': scenes, 'selling_points': points, 'weaknesses': bad, 'compare_scores': scores, 'features': features, 'specs': specs, 'description': description}  
  
PRODUCTS = [ 
    p('星岭', 'X2', '星岭 X2', 'smartphone', '均衡旗舰', '拍照和体验都很稳', '中高端', 4599, 4199, 4899, ['学生', '年轻上班族'], ['日常通勤', '旅行拍照'], ['性能均衡', '主摄稳定', '充电速度快'], ['长焦表现一般'], score(8.7, 8.8, 8.2, 8.4, 8.3), ['120Hz 高刷屏', '立体声双扬声器', '80W 快充'], {'芯片': '星云 S2', '内存': '12GB+256GB', '电池': '5000mAh'}, '一款适合大多数用户的均衡旗舰手机。', own=True, featured=True, priority=95),  
    p('星岭', 'X2 Pro', '星岭 X2 Pro', 'smartphone', '影像旗舰', '夜景和人像更出色', '高端', 5799, 5399, 6199, ['内容创作者', '摄影爱好者'], ['夜景拍摄', '旅行记录'], ['主摄素质强', '夜景纯净', '机身质感好'], ['机身偏重'], score(8.9, 9.5, 8.1, 8.8, 7.4), ['潜望长焦', '无线充电', '旗舰屏幕'], {'芯片': '星云 S2 Pro', '内存': '16GB+512GB', '电池': '5100mAh'}, '更偏向影像表达的高端旗舰。', own=True, featured=True, priority=99),  
    p('星岭', 'X2 青春版', '星岭 X2 青春版', 'smartphone', '轻薄中端', '轻一点也够用', '中端', 2999, 2699, 3199, ['学生', '家庭用户'], ['社交娱乐', '日常使用'], ['机身轻薄', '续航省心', '系统干净'], ['拍照能力普通'], score(7.2, 6.8, 8.4, 7.0, 8.9), ['轻量机身', '5000mAh 电池', '双扬声器'], {'芯片': '星云 S2 Lite', '内存': '8GB+256GB', '电池': '5000mAh'}, '适合预算有限但希望体验轻快的用户。', own=True, featured=False, priority=70),  
    p('曜石', 'N9 Ultra', '曜石 N9 Ultra', 'smartphone', '影像旗舰', '主打大底影像', '高端', 5999, 5599, 6399, ['摄影用户', '高端换机用户'], ['人像拍摄', '城市夜景'], ['相机素质强', '屏幕亮度高'], ['续航中规中矩'], score(8.8, 9.6, 7.8, 9.1, 7.2), ['一英寸主摄', '高亮直屏'], {'芯片': '曜石 N9 Max', '内存': '16GB+512GB'}, '重视拍照能力的用户会优先考虑这款。', priority=92, featured=True),  
    p('极锋', 'V10', '极锋 V10', 'smartphone', '性能旗舰', '高帧游戏更稳', '中高端', 4899, 4499, 5199, ['手游玩家', '重度用户'], ['大型游戏', '多任务处理'], ['持续性能强', '游戏帧率高'], ['拍照调校一般'], score(9.3, 7.6, 8.6, 8.7, 7.8), ['电竞散热', '144Hz 屏幕'], {'芯片': '极锋 V10 Elite', '内存': '16GB+256GB'}, '偏游戏和性能释放的旗舰机型。', priority=80),  
    p('星岭', '灵越 Air 14', '星岭 灵越 Air 14', 'laptop', '轻薄本', '通勤办公很轻松', '中端', 5299, 4899, 5599, ['上班族', '学生'], ['办公', '出差'], ['机身轻', '续航长', '键盘安静'], ['图形性能一般'], score(7.8, None, 8.9, 8.1, 9.3), ['14 英寸 2.5K', '70Wh 电池', '1.25kg'], {'处理器': '锐龙 7 8845HS', '内存': '32GB', '硬盘': '1TB'}, '适合日常办公和跨城出差的轻薄本。', own=True, featured=True, priority=93),  
    p('星岭', '创作本 Pro 16', '星岭 创作本 Pro 16', 'laptop', '创作本', '大屏剪辑更舒服', '高端', 8299, 7899, 8699, ['设计师', '视频创作者'], ['视频剪辑', '多窗口办公'], ['处理器强', '屏幕大', '接口齐全'], ['便携性一般'], score(9.1, None, 8.0, 9.0, 6.8), ['16 英寸 3K 屏', '独显', '99Wh 电池'], {'处理器': '酷睿 Ultra 9', '内存': '32GB', '硬盘': '1TB'}, '适合创作和重度生产力场景。', own=True, featured=True, priority=97),  
    p('曜石', '游戏本 G16', '曜石 游戏本 G16', 'laptop', '游戏本', '高性能独显本', '高性能', 8799, 8399, 9199, ['游戏玩家', '三维创作者'], ['3A 游戏', '三维渲染'], ['独显性能强', '高刷屏流畅'], ['机身较重', '风扇噪音大'], score(9.5, None, 6.8, 8.8, 5.9), ['RTX 4070', '240Hz 高刷'], {'处理器': 'i9 HX', '内存': '32GB', '硬盘': '1TB'}, '更适合追求性能上限的用户。', featured=True, priority=91),  
    p('云图', '轻享 14', '云图 轻享 14', 'laptop', '轻薄本', '价格和重量都友好', '入门中端', 4599, 4299, 4899, ['学生', '轻办公用户'], ['网课', '文档处理'], ['价格友好', '便携性好'], ['屏幕素质普通'], score(7.0, None, 8.2, 7.4, 9.0), ['1.3kg 机身', '长续航'], {'处理器': '锐龙 5', '内存': '16GB', '硬盘': '512GB'}, '适合预算有限的轻办公用户。', priority=74),  
    p('极锋', '全能本 15', '极锋 全能本 15', 'laptop', '全能本', '办公娱乐都能兼顾', '中高端', 6399, 5999, 6799, ['家庭用户', '综合办公用户'], ['办公', '修图', '娱乐'], ['配置均衡', '接口丰富'], ['机身不算轻'], score(8.4, None, 8.1, 8.2, 7.0), ['15.6 英寸大屏', '双风扇散热'], {'处理器': '酷睿 Ultra 7', '内存': '32GB', '硬盘': '1TB'}, '兼顾办公和娱乐的全能型笔记本。', priority=82), 
    p('星岭', '星图 Pad 12', '星岭 星图 Pad 12', 'tablet', '学习平板', '记笔记和追剧都顺手', '中端', 2899, 2599, 3099, ['学生', '年轻上班族'], ['课堂笔记', '追剧'], ['手写笔体验好', '屏幕均衡'], ['相机一般'], score(7.6, None, 8.7, 8.3, 8.4), ['11.8 英寸屏幕', '手写笔支持'], {'内存': '8GB+256GB', '电池': '9000mAh'}, '一款兼顾学习和娱乐的平板。', own=True, featured=True, priority=88),  
    p('星岭', '星图 Pad Pro 13', '星岭 星图 Pad Pro 13', 'tablet', '创作平板', '大屏效率更高', '高端', 4299, 3999, 4599, ['创作者', '轻办公用户'], ['绘画', '轻办公'], ['大屏幕', '扬声器好', '多任务顺滑'], ['配件价格高'], score(8.5, None, 8.6, 9.1, 7.7), ['13 英寸 144Hz', '键盘磁吸'], {'内存': '12GB+256GB', '电池': '10000mAh'}, '适合需要大屏和更强生产力的用户。', own=True, featured=True, priority=94),  
    p('曜石', '画板 Tab 13', '曜石 画板 Tab 13', 'tablet', '创作平板', '屏幕色彩更专业', '高端', 4699, 4399, 4999, ['插画师', '设计师'], ['绘画', '修图'], ['屏幕色彩准', '手写延迟低'], ['系统生态一般'], score(8.4, None, 8.0, 9.3, 7.4), ['高色域屏', '专业手写笔'], {'内存': '12GB+512GB', '电池': '9800mAh'}, '更适合偏创作和绘画的平板用户。', featured=True, priority=90),  
    p('云图', '学习屏 Tab 11', '云图 学习屏 Tab 11', 'tablet', '学习平板', '网课和阅读更省心', '入门中端', 2399, 2099, 2599, ['学生', '家长'], ['网课', '阅读'], ['价格友好', '护眼模式实用'], ['外放一般'], score(7.0, None, 8.2, 7.8, 8.6), ['护眼模式', '轻薄机身'], {'内存': '8GB+128GB', '电池': '8600mAh'}, '更适合学生日常学习使用。', priority=68),  
    p('极锋', '娱乐板 Max 12', '极锋 娱乐板 Max 12', 'tablet', '影音平板', '看剧和游戏都更爽', '中高端', 3299, 2999, 3499, ['影音用户', '轻游戏用户'], ['追剧', '轻游戏'], ['扬声器强', '性能更好'], ['重量略高'], score(8.2, None, 8.1, 8.8, 7.1), ['四扬声器', '高刷屏'], {'内存': '12GB+256GB', '电池': '9500mAh'}, '适合更注重影音体验的平板用户。', priority=79),  
    p('星岭', 'Watch S', '星岭 Watch S', 'watch', '健康手表', '入门也够实用', '入门', 1099, 899, 1199, ['健身新手', '家庭用户'], ['日常佩戴', '基础运动'], ['佩戴轻', '健康监测够用'], ['应用生态一般'], score(6.5, None, 8.4, 7.4, 9.0), ['轻量表身', '7 天续航'], {'重量': '33g'}, '适合第一次购买智能手表的用户。', own=True, priority=65),  
    p('星岭', 'Watch Pro', '星岭 Watch Pro', 'watch', '运动手表', '跑步和户外更专业', '中高端', 1899, 1699, 1999, ['跑者', '户外用户'], ['跑步', '徒步'], ['续航长', '定位更准'], ['机身更厚'], score(7.2, None, 9.2, 8.2, 7.6), ['双频定位', '14 天续航'], {'重量': '47g'}, '适合更看重运动和续航的用户。', own=True, featured=True, priority=85),  
    p('曜石', 'Run Pro', '曜石 Run Pro', 'watch', '跑步手表', '心率和配速反馈更细', '中高端', 1999, 1799, 2099, ['跑步爱好者', '马拉松用户'], ['跑步训练', '体能监测'], ['训练数据丰富', '屏幕清晰'], ['系统上手稍慢'], score(7.0, None, 8.8, 8.7, 7.8), ['专业跑步课程', '双频定位'], {'重量': '42g'}, '偏向专业跑步训练的智能手表。', featured=True, priority=83),  
    p('云图', 'Watch Air', '云图 Watch Air', 'watch', '轻薄手表', '日常佩戴更轻盈', '中端', 1399, 1199, 1499, ['上班族', '日常佩戴用户'], ['日常佩戴', '轻运动'], ['机身薄', '屏幕好看'], ['续航偏短'], score(6.4, None, 7.1, 8.4, 9.1), ['薄型表身', '高亮屏'], {'重量': '30g'}, '更适合喜欢轻薄佩戴感的用户。', priority=69),  
    p('极锋', '户外表 X', '极锋 户外表 X', 'watch', '户外手表', '耐用和续航是强项', '高端', 2299, 2099, 2499, ['户外用户', '露营用户'], ['徒步', '露营', '越野'], ['机身耐用', '续航很长'], ['表身偏厚重'], score(7.1, None, 9.4, 7.9, 6.9), ['军规防护', '18 天续航'], {'重量': '52g'}, '适合更偏户外运动的用户。', priority=81), 
    p('星岭', 'Buds Air', '星岭 Buds Air', 'earbuds', '日常耳机', '轻巧耐听', '入门', 699, 599, 799, ['学生', '通勤用户'], ['通勤', '语音通话'], ['佩戴轻', '连接稳定'], ['降噪一般'], score(6.0, None, 7.8, 6.8, 9.4), ['轻量耳机盒', '双设备连接'], {'续航': '28 小时'}, '适合预算有限的日常通勤用户。', own=True, priority=60),  
    p('星岭', 'Buds Pro', '星岭 Buds Pro', 'earbuds', '降噪耳机', '通勤降噪更安静', '中端', 1199, 999, 1299, ['通勤用户', '办公室用户'], ['地铁通勤', '办公室通话'], ['主动降噪更强', '通话更清晰'], ['低频量感一般'], score(6.6, None, 8.1, 7.5, 8.8), ['自适应降噪', '三麦通话'], {'续航': '36 小时'}, '适合通勤和会议通话都比较多的用户。', own=True, featured=True, priority=84),  
    p('曜石', '降噪豆 X', '曜石 降噪豆 X', 'earbuds', '旗舰降噪耳机', '降噪深度更强', '中高端', 1399, 1199, 1499, ['地铁通勤用户', '音乐爱好者'], ['地铁', '飞机'], ['降噪强', '声音厚实'], ['佩戴时间长会累'], score(6.8, None, 7.9, 7.8, 7.6), ['深度降噪', '大尺寸单元'], {'续航': '32 小时'}, '更适合优先看重降噪深度的用户。', priority=82),  
    p('云图', '清听 Air', '云图 清听 Air', 'earbuds', '半入耳耳机', '佩戴轻松不压耳', '中端', 899, 799, 999, ['上班族', '轻度听歌用户'], ['办公', '通话'], ['半入耳舒适', '人声清晰'], ['降噪较弱'], score(5.8, None, 7.5, 7.0, 9.1), ['半入耳设计', '通话优化'], {'续航': '30 小时'}, '更适合长时间佩戴和通话。', priority=66),  
    p('极锋', '运动耳夹', '极锋 运动耳夹', 'earbuds', '运动耳机', '跑跳也更稳', '中端', 999, 899, 1099, ['健身用户', '跑步用户'], ['跑步', '健身'], ['佩戴稳', '防汗能力好'], ['音质表现一般'], score(6.2, None, 7.6, 6.9, 9.3), ['开放式耳夹', '防汗涂层'], {'续航': '26 小时'}, '更适合运动场景使用。', priority=64),  
]  
  
PRICE_TEMPLATES = {  
    '京东': [('标价', 1.04), ('活动价', 0.98), ('券后价', 0.95)],  
    '天猫': [('标价', 1.03), ('活动价', 0.99)],  
    '拼多多': [('活动价', 0.96), ('补贴价', 0.91)],  
    '线下门店': [('门店价', 1.00), ('到店价', 0.97)],  
}  
  
def build_snapshots(product_id, guide_price, platform_seed):  
    rows = []  
    for platform, items in PRICE_TEMPLATES.items():  
        base_ratio = 1 + (((platform_seed + len(platform)) % 5 - 2) * 0.006)  
        for index, (price_type, ratio, promotion_text) in enumerate(items):  
            current_price = round(guide_price * ratio * base_ratio)  
            original_price = round(max(current_price, guide_price * (1.02 if price_type != '标价' else 1.0)))  
            rows.append(ProductPriceSnapshot(product_id=product_id, platform=platform, seller_type='官方' if platform in {'京东', '天猫'} else ('平台' if platform == '拼多多' else '门店'), store_name='京东自营旗舰店' if platform == '京东' else ('天猫官方旗舰店' if platform == '天猫' else ('拼多多百亿补贴' if platform == '拼多多' else '城市体验店')), region='中国大陆', price_type=price_type, current_price=float(current_price), original_price=float(original_price), promotion_text=promotion_text, in_stock=not (price_type in {'coupon_after', 'subsidy_after'} and (product_id + platform_seed)%4==0), is_primary=(platform in {'京东', '天猫'} and price_type == 'sale') or (platform == '拼多多' and price_type == 'subsidy_after') or (platform == '线下门店' and price_type == 'store_price'), snapshot_time=NOW - timedelta(hours=index * 8 + platform_seed % 7), valid_from=NOW - timedelta(days=1), valid_to=NOW + timedelta(days=6 - index), currency='CNY', note='中文种子价格快照'))  
    return rows  
  
async def reseed():  
    async with AsyncSessionLocal() as session:  
        await session.execute(delete(ProductPriceSnapshot))  
        await session.execute(delete(Product))  
        await session.commit()  
        rows = [Product(**payload) for payload in PRODUCTS]  
        session.add_all(rows)  
        await session.commit()  
        for index, row in enumerate(rows):  
            session.add_all(build_snapshots(row.id, row.guide_price, index + 3))  
        await session.commit()  
    await engine.dispose()  
  
if __name__ == '__main__':  
    asyncio.run(reseed()) 
