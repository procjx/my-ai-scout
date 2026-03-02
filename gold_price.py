#!/usr/bin/env python3
"""
黄金指数监控 - 获取新浪财经指数点位（非价格）
"""

import os
import requests
from datetime import datetime


def get_gold_index():
    """
    获取新浪财经黄金指数（非实际价格）
    指数基准：2019年12月31日 = 1000点
    """
    try:
        # 沪金主连指数
        url = "https://hq.sinajs.cn/list=AU0"
        headers = {
            "Referer": "https://finance.sina.com.cn",
            "User-Agent": "Mozilla/5.0"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'gb2312'
        
        data_str = response.text.split('"')[1]
        parts = data_str.split(',')
        
        # 新浪返回的字段中，第3个字段（索引3）在页面上显示为指数
        # 但实际API返回的是元/克价格，我们需要计算指数
        # 或者使用新浪的指数API
        
        # 方法1：通过新浪行情页面抓取指数（推荐）
        index_url = "https://stock.finance.sina.com.cn/futures/api/json.php/Cffex_FuturesService.getCffexFuturesDailyKLine?symbol=AU0"
        idx_response = requests.get(index_url, headers=headers, timeout=10)
        idx_data = idx_response.json()
        
        if idx_data and len(idx_data) > 0:
            latest = idx_data[-1]  # 最新数据
            index_point = float(latest.get("close", 0))
            
            # 计算涨跌
            prev = idx_data[-2] if len(idx_data) > 1 else latest
            prev_close = float(prev.get("close", index_point))
            change = index_point - prev_close
            change_percent = (change / prev_close) * 100 if prev_close > 0 else 0
            
            return {
                "index": round(index_point, 3),      # 1187.180
                "change": round(change, 3),
                "change_percent": round(change_percent, 2),
                "open": float(latest.get("open", 0)),
                "high": float(latest.get("high", 0)),
                "low": float(latest.get("low", 0)),
                "unit": "点",
                "base": "1000点（2019-12-31基准）",
                "note": "这是指数点位，不是元/克价格"
            }
            
    except Exception as e:
        print(f"方法1失败: {e}")
    
    # 方法2：备用 - 直接计算指数（如果知道基准）
    try:
        url = "https://hq.sinajs.cn/list=AU0"
        headers = {"Referer": "https://finance.sina.com.cn"}
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'gb2312'
        
        data_str = response.text.split('"')[1]
        parts = data_str.split(',')
        
        # 当前金价（元/克）
        current_price = float(parts[3])
        # 基准金价（约380元/克，2019年底）
        base_price = 380.0
        
        # 计算指数
        index_point = (current_price / base_price) * 1000
        
        return {
            "index": round(index_point, 3),
            "current_price": current_price,
            "base_price": base_price,
            "unit": "点（估算）",
            "base": "1000点（2019-12-31基准，估算）",
            "note": "基于2019年底金价380元/克估算"
        }
        
    except Exception as e:
        print(f"方法2也失败: {e}")
        return None


def send_index_to_feishu(data):
    """
    发送指数到飞书
    """
    webhook_url = os.environ.get("FEISHU_WEBHOOK_URL")
    if not webhook_url:
        print("错误: 未设置 FEISHU_WEBHOOK_URL")
        return False
    
    trend = "📈" if data.get("change", 0) >= 0 else "📉"
    color = "green" if data.get("change", 0) >= 0 else "red"
    sign = "+" if data.get("change", 0) >= 0 else ""
    
    message = {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": f"{trend} 黄金指数监控"
                },
                "template": color
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**📊 指数点位: {data['index']} 点**\n\n"
                                  f"**📈 涨跌:** {sign}{data.get('change', 0)} ({sign}{data.get('change_percent', 0)}%)\n"
                                  f"**⬆️ 最高:** {data.get('high', '--')} 点\n"
                                  f"**⬇️ 最低:** {data.get('low', '--')} 点\n"
                                  f"**📉 开盘:** {data.get('open', '--')} 点"
                    }
                },
                {
                    "tag": "hr"
                },
                {
                    "tag": "note",
                    "elements": [
                        {
                            "tag": "plain_text",
                            "content": f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                                      f"📌 基准: {data['base']}\n"
                                      f"💡 {data['note']}\n"
                                      f"🔗 新浪页面: https://finance.sina.com.cn/futures/quotes/AU0.shtml"
                        }
                    ]
                }
            ]
        }
    }
    
    try:
        response = requests.post(
            webhook_url,
            headers={"Content-Type": "application/json"},
            json=message,
            timeout=10
        )
        return response.json().get("code") == 0
    except Exception as e:
        print(f"发送失败: {e}")
        return False


def main():
    print("=" * 50)
    print("🚀 黄金指数监控")
    print("目标：获取指数点位（如1187.180）")
    print("=" * 50)
    
    data = get_gold_index()
    if not data:
        print("❌ 获取失败")
        exit(1)
    
    print(f"✅ 获取成功")
    print(f"   指数: {data['index']} {data['unit']}")
    if 'current_price' in data:
        print(f"   对应金价: {data['current_price']} 元/克")
    print(f"   基准: {data['base']}")
    
    if send_index_to_feishu(data):
        print("✅ 发送成功")
    else:
        print("❌ 发送失败")
        exit(1)


if __name__ == "__main__":
    main()
