#!/usr/bin/env python3
"""
黄金人民币价格监控 - 飞书机器人版
每小时获取黄金价格并推送到飞书
"""

import os
import json
import requests
from datetime import datetime


def get_gold_price_cny():
    """
    获取黄金人民币价格
    使用新浪财经API（免费，无需认证）
    """
    try:
        # 新浪财经黄金人民币报价 (AU0 上海黄金交易所)
        url = "https://hq.sinajs.cn/list=AU0"
        headers = {
            "Referer": "https://finance.sina.com.cn",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'gb2312'
        
        # 解析返回数据: var hq_str_AU0="黄金连续,...
        data_str = response.text.split('"')[1]
        data_parts = data_str.split(',')
        
        # 提取关键数据
        current_price = float(data_parts[2])      # 最新价
        open_price = float(data_parts[5])         # 开盘价
        high_price = float(data_parts[6])         # 最高价
        low_price = float(data_parts[7])         # 最低价
        prev_close = float(data_parts[4])         # 昨收
        
        # 计算涨跌幅
        change = current_price - prev_close
        change_percent = (change / prev_close) * 100
        
        return {
            "current": round(current_price, 2),
            "open": round(open_price, 2),
            "high": round(high_price, 2),
            "low": round(low_price, 2),
            "change": round(change, 2),
            "change_percent": round(change_percent, 2),
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source": "上海黄金交易所"
        }
        
    except Exception as e:
        print(f"获取黄金价格失败: {e}")
        return None


def send_to_feishu(price_data):
    """
    发送消息到飞书机器人
    """
    webhook_url = os.environ.get("FEISHU_WEBHOOK_URL")
    if not webhook_url:
        print("错误: 未设置 FEISHU_WEBHOOK_URL 环境变量")
        return False
    
    # 判断涨跌颜色
    trend_emoji = "📈" if price_data["change"] >= 0 else "📉"
    trend_color = "green" if price_data["change"] >= 0 else "red"
    change_sign = "+" if price_data["change"] >= 0 else ""
    
    # 构建飞书卡片消息
    card_message = {
        "msg_type": "interactive",
        "card": {
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": f"{trend_emoji} 黄金价格实时播报"
                },
                "template": trend_color
            },
            "elements": [
                {
                    "tag": "div",
                    "fields": [
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**💰 最新价格**\n{price_data['current']} 元/克"
                            }
                        },
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**📊 涨跌幅**\n{change_sign}{price_data['change']} ({change_sign}{price_data['change_percent']}%)"
                            }
                        }
                    ]
                },
                {
                    "tag": "div",
                    "fields": [
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**⬆️ 最高价**\n{price_data['high']} 元/克"
                            }
                        },
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**⬇️ 最低价**\n{price_data['low']} 元/克"
                            }
                        }
                    ]
                },
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**🕐 数据时间:** {price_data['time']}\n**🏦 数据来源:** {price_data['source']}"
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
                            "content": "⏰ 每小时自动更新 | 由 GitHub Actions 推送"
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
            json=card_message,
            timeout=10
        )
        result = response.json()
        
        if result.get("code") == 0:
            print(f"✅ 消息发送成功: {price_data['current']}元")
            return True
        else:
            print(f"❌ 发送失败: {result}")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False


def main():
    print("=" * 50)
    print("🚀 黄金价格监控启动")
    print(f"⏰ 当前时间: {datetime.now()}")
    print("=" * 50)
    
    # 获取价格
    price_data = get_gold_price_cny()
    if not price_data:
        # 发送错误通知
        send_error_notification("获取黄金价格数据失败")
        return
    
    print(f"💰 当前价格: {price_data['current']} 元/克")
    print(f"📊 涨跌幅: {price_data['change']} ({price_data['change_percent']}%)")
    
    # 发送到飞书
    success = send_to_feishu(price_data)
    
    if success:
        print("✅ 任务完成")
    else:
        print("❌ 任务失败")
        exit(1)


def send_error_notification(error_msg):
    """发送错误通知"""
    webhook_url = os.environ.get("FEISHU_WEBHOOK_URL")
    if not webhook_url:
        return
    
    message = {
        "msg_type": "text",
        "content": {
            "text": f"⚠️ 黄金价格监控异常\n\n错误信息: {error_msg}\n时间: {datetime.now()}"
        }
    }
    
    try:
        requests.post(webhook_url, json=message, timeout=5)
    except:
        pass


if __name__ == "__main__":
    main()
