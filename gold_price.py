#!/usr/bin/env python3
"""
新浪期货 - 沪金主连(AU0) 完整数据抓取
URL: https://finance.sina.com.cn/futures/quotes/AU0.shtml
"""

import os
import re
import requests
from datetime import datetime


def get_sina_futures_au0():
    """
    从新浪财经期货页面抓取沪金主连完整数据
    """
    url = "https://finance.sina.com.cn/futures/quotes/AU0.shtml"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = 'utf-8'
        html = response.text
        
        data = {}
        
        # 1. 抓取顶部大数字（当前指数、涨跌、涨跌幅）
        # 格式: 1187.180 +42.220 +3.69%
        top_pattern = r'<div[^>]*class=["\']price["\'][^>]*>.*?([\d\.]+).*?([\+\-][\d\.]+).*?([\+\-][\d\.]+%)'
        top_match = re.search(top_pattern, html, re.DOTALL)
        if top_match:
            data['current_index'] = top_match.group(1)      # 1187.180
            data['change'] = top_match.group(2)              # +42.220
            data['change_percent'] = top_match.group(3)      # +3.69%
        else:
            # 备用：直接查找大数字
            big_num = re.search(r'>(\d{4}\.\d{3})<', html)
            if big_num:
                data['current_index'] = big_num.group(1)
        
        # 2. 抓取时间
        time_pattern = r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})'
        time_match = re.search(time_pattern, html)
        if time_match:
            data['update_time'] = time_match.group(1)        # 2026-03-02 11:30:00
        
        # 3. 抓取表格数据（最新价、开盘价、最高价等）
        # 方法：查找所有包含"最新价"、"开盘价"等的标签
        patterns = {
            '最新价': r'最新价[：:]?\s*<[^>]*>\s*([\d\.]+)',
            '开盘价': r'开盘价[：:]?\s*<[^>]*>\s*([\d\.]+)',
            '最高价': r'最高价[：:]?\s*<[^>]*>\s*([\d\.]+)',
            '最低价': r'最低价[：:]?\s*<[^>]*>\s*([\d\.]+)',
            '结算价': r'结算价[：:]?\s*<[^>]*>\s*([\d\.]+)',
            '昨结算': r'昨结算[：:]?\s*<[^>]*>\s*([\d\.]+)',
            '持仓量': r'持仓量[：:]?\s*<[^>]*>\s*([\d,]+)',
            '成交量': r'成交量[：:]?\s*<[^>]*>\s*([\d,]+)',
            '买价': r'买\s*价[：:]?\s*<[^>]*>\s*([\d\.]+)',
            '卖价': r'卖\s*价[：:]?\s*<[^>]*>\s*([\d\.]+)',
            '买量': r'买\s*量[：:]?\s*<[^>]*>\s*(\d+)',
            '卖量': r'卖\s*量[：:]?\s*<[^>]*>\s*(\d+)',
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, html)
            if match:
                # 移除逗号（持仓量、成交量可能有逗号）
                value = match.group(1).replace(',', '')
                data[key] = value
        
        # 4. 抓取合约信息
        contract_pattern = r'(AU\d{4})'  # 如 AU2504
        contract_match = re.search(contract_pattern, html)
        if contract_match:
            data['contract'] = contract_match.group(1)
        
        # 5. 抓取交易所
        exchange_pattern = r'(上海期货交易所|上期所)'
        exchange_match = re.search(exchange_pattern, html)
        if exchange_match:
            data['exchange'] = exchange_match.group(1)
        
        # 6. 抓取美元/盎司价格（如果有）
        usd_pattern = r'黄金\(美元/盎司\)[^\d]*(\d+\.\d+)'
        usd_match = re.search(usd_pattern, html)
        if usd_match:
            data['usd_per_ounce'] = usd_match.group(1)
        
        return data
        
    except Exception as e:
        print(f"抓取失败: {e}")
        return None


def format_data(data):
    """
    格式化数据用于显示
    """
    if not data:
        return "无数据"
    
    lines = []
    lines.append("=" * 50)
    lines.append("📊 沪金主连(AU0) 行情数据")
    lines.append("=" * 50)
    
    # 主要价格
    lines.append(f"\n💰 指数点位: {data.get('current_index', '--')} 点")
    lines.append(f"📈 涨跌: {data.get('change', '--')} ({data.get('change_percent', '--')})")
    lines.append(f"🕐 更新时间: {data.get('update_time', '--')}")
    
    # 详细数据
    lines.append(f"\n📋 详细行情:")
    lines.append(f"  最新价: {data.get('最新价', '--')}")
    lines.append(f"  开盘价: {data.get('开盘价', '--')}")
    lines.append(f"  最高价: {data.get('最高价', '--')}")
    lines.append(f"  最低价: {data.get('最低价', '--')}")
    lines.append(f"  昨结算: {data.get('昨结算', '--')}")
    
    # 交易数据
    lines.append(f"\n📊 交易数据:")
    lines.append(f"  成交量: {data.get('成交量', '--')} 手")
    lines.append(f"  持仓量: {data.get('持仓量', '--')} 手")
    
    # 买卖盘
    lines.append(f"\n💹 买卖盘:")
    lines.append(f"  买价: {data.get('买价', '--')}  买量: {data.get('买量', '--')}")
    lines.append(f"  卖价: {data.get('卖价', '--')}  卖量: {data.get('卖量', '--')}")
    
    # 其他
    if 'usd_per_ounce' in data:
        lines.append(f"\n🌍 国际金价: {data['usd_per_ounce']} 美元/盎司")
    
    lines.append("=" * 50)
    
    return "\n".join(lines)


def send_to_feishu(data):
    """
    发送完整数据到飞书
    """
    webhook_url = os.environ.get("FEISHU_WEBHOOK_URL")
    if not webhook_url:
        print("错误: 未设置 FEISHU_WEBHOOK_URL")
        return False
    
    # 判断涨跌颜色
    change_str = data.get('change', '0')
    if change_str.startswith('-'):
        trend = "📉"
        color = "red"
    else:
        trend = "📈"
        color = "green"
    
    # 构建富文本消息
    card_message = {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": f"{trend} 沪金主连(AU0) 行情"
                },
                "template": color
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**💰 指数点位: {data.get('current_index', '--')} 点**\n"
                                  f"**📈 涨跌: {data.get('change', '--')} ({data.get('change_percent', '--')})**\n"
                                  f"🕐 {data.get('update_time', '--')}"
                    }
                },
                {"tag": "hr"},
                {
                    "tag": "div",
                    "fields": [
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**最新价**\n{data.get('最新价', '--')}"
                            }
                        },
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**开盘价**\n{data.get('开盘价', '--')}"
                            }
                        },
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**最高价**\n{data.get('最高价', '--')}"
                            }
                        },
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**最低价**\n{data.get('最低价', '--')}"
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
                                "content": f"**成交量**\n{data.get('成交量', '--')} 手"
                            }
                        },
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**持仓量**\n{data.get('持仓量', '--')} 手"
                            }
                        }
                    ]
                },
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**💹 买卖盘**\n"
                                  f"买 {data.get('买价', '--')} ({data.get('买量', '--')}手) | "
                                  f"卖 {data.get('卖价', '--')} ({data.get('卖量', '--')}手)"
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
                            "content": f"📌 数据来源: 新浪财经期货\n"
                                      f"🔗 {data.get('url', 'https://finance.sina.com.cn/futures/quotes/AU0.shtml')}\n"
                                      f"⚠️ 指数基准: 1000点（2019-12-31）"
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
        return result.get("code") == 0
        
    except Exception as e:
        print(f"发送失败: {e}")
        return False


def main():
    print("🚀 开始抓取新浪期货 - 沪金主连(AU0) 数据...")
    print(f"⏰ {datetime.now()}")
    print("-" * 50)
    
    data = get_sina_futures_au0()
    
    if not data:
        print("❌ 抓取失败")
        exit(1)
    
    # 打印格式化数据
    print(format_data(data))
    
    # 发送到飞书
    print("\n📤 发送到飞书...")
    if send_to_feishu(data):
        print("✅ 发送成功")
    else:
        print("❌ 发送失败")
        exit(1)


if __name__ == "__main__":
    main()
