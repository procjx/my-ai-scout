#!/usr/bin/env python3
"""
黄金价格监控 - 正确解析新浪数据
"""

import os
import requests
from datetime import datetime


def get_gold_price_correct():
    """
    正确获取黄金价格（区分指数和实际价格）
    """
    try:
        # 获取上海黄金交易所AU9999现货价格
        url = "https://hq.sinajs.cn/list=AU0"
        headers = {
            "Referer": "https://finance.sina.com.cn",
            "User-Agent": "Mozilla/5.0"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'gb2312'
        
        # 解析数据
        # var hq_str_AU0="黄金连续,581.50,581.00,582.30,583.00,580.50,578.00,582.30,..."
        # 字段说明：名称, 开盘价, 昨收, 最新价, 最高, 最低, ...
        data_str = response.text.split('"')[1]
        parts = data_str.split(',')
        
        name = parts[0]           # 黄金连续
        open_price = float(parts[1])      # 开盘价
        prev_close = float(parts[2])      # 昨收价（昨日收盘价）
        current = float(parts[3])         # 最新价 ✅ 这是实际价格！
        high = float(parts[4])            # 最高价
        low = float(parts[5])             # 最低价
        
        # 计算涨跌
        change = current - prev_close
        change_percent = (change / prev_close) * 100
        
        return {
            "name": name,
            "current": current,           # ✅ 582.30 元/克（正确）
            "open": open_price,
            "high": high,
            "low": low,
            "prev_close": prev_close,
            "change": round(change, 2),
            "change_percent": round(change_percent, 2),
            "unit": "元/克",
            "note": "这是实际黄金价格，不是页面显示的指数1187"
        }
        
    except Exception as e:
        print(f"获取失败: {e}")
        return None


def send_to_feishu(price_data):
    """
    发送正确价格到飞书
    """
    webhook_url = os.environ.get("FEISHU_WEBHOOK_URL")
    if not webhook_url:
        print("错误: 未设置 FEISHU_WEBHOOK_URL")
        return False
    
    trend = "📈" if price_data["change"] >= 0 else "📉"
    color = "green" if price_data["change"] >= 0 else "red"
    sign = "+" if price_data["change"] >= 0 else ""
    
    message = {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": f"{trend} 黄金价格监控"
                },
                "template": color
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**💰 最新价: {price_data['current']} 元/克**\n\n"
                                  f"**📊 涨跌:** {sign}{price_data['change']} ({sign}{price_data['change_percent']}%)\n"
                                  f"**⬆️ 最高:** {price_data['high']} 元/克\n"
                                  f"**⬇️ 最低:** {price_data['low']} 元/克\n"
                                  f"**📈 昨收:** {price_data['prev_close']} 元/克"
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
                                      f"💡 数据来源: 上海黄金交易所 AU9999\n"
                                      f"⚠️ 注意：新浪页面显示的1187是指数，不是价格！"
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
    print("🚀 黄金价格监控（正确版）")
    print("=" * 50)
    
    data = get_gold_price_correct()
    if not data:
        print("❌ 获取失败")
        exit(1)
    
    print(f"✅ 获取成功")
    print(f"   品种: {data['name']}")
    print(f"   最新价: {data['current']} {data['unit']}")
    print(f"   涨跌: {data['change']} ({data['change_percent']}%)")
    print(f"   备注: {data['note']}")
    
    if send_to_feishu(data):
        print("✅ 发送成功")
    else:
        print("❌ 发送失败")
        exit(1)


if __name__ == "__main__":
    main()
