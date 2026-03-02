#!/usr/bin/env python3
"""
新浪期货API - 沪金主连(AU0) 数据获取
使用新浪官方API，稳定可靠
"""

import os
import json
import requests
from datetime import datetime


def get_sina_futures_api():
    """
    使用新浪期货API获取数据（非页面抓取）
    """
    # 新浪期货行情API
    # list参数：AU0 表示沪金主连
    url = "https://hq.sinajs.cn/list=AU0"
    
    headers = {
        "Referer": "https://finance.sina.com.cn",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'gb2312'  # 新浪返回GB2312编码
        
        # 返回格式: var hq_str_AU0="黄金连续,1150.160,1144.960,1187.180,1187.980,1148.620,1187.160,1187.180,273719,153924,1187.180,1,1187.180,2,1187.180,3,1187.180,4,1187.180,5,1187.180,6,1187.180,7,1187.180,8,1187.180,9,1187.180,10,1187.180,11,1187.180,12,1187.180,13,1187.180,14,1187.180,15,1187.180,16,1187.180,17,1187.180,18,1187.180,19,1187.180,20,1187.180,21,1187.180,22,1187.180,23,1187.180,24,1187.180,25,1187.180,26,1187.180,27,1187.180,28,1187.180,29,2026-03-02,11:30:00,00";
        
        text = response.text
        
        # 提取引号内的数据
        if 'hq_str_AU0=' not in text:
            print("API返回异常:", text[:200])
            return None
        
        data_str = text.split('"')[1]
        parts = data_str.split(',')
        
        if len(parts) < 30:
            print("数据字段不足:", len(parts))
            return None
        
        # 解析字段（根据新浪期货数据格式）
        # 参考: https://blog.csdn.net/afgasdg/article/details/8606484
        data = {
            'name': parts[0],                    # 黄金连续
            '开盘价': float(parts[1]),            # 1150.160
            '昨结算': float(parts[2]),            # 1144.960（昨结算价）
            '最新价': float(parts[3]),            # 1187.180（当前指数）
            '最高价': float(parts[4]),            # 1187.980
            '最低价': float(parts[5]),            # 1148.620
            '买价': float(parts[6]),              # 1187.160
            '卖价': float(parts[7]),              # 1187.180
            '成交量': int(parts[8]),              # 273719（手）
            '持仓量': int(parts[9]),              # 153924（手）
            '更新时间': f"{parts[-3]} {parts[-2]}",  # 2026-03-02 11:30:00
        }
        
        # 计算涨跌（最新价 - 昨结算）
        data['涨跌'] = round(data['最新价'] - data['昨结算'], 3)
        data['涨跌幅'] = round((data['涨跌'] / data['昨结算']) * 100, 2)
        
        # 买卖量（在parts[10]开始，每4个一组：买价,买量,卖价,卖量）
        if len(parts) > 11:
            data['买量'] = int(parts[11]) if parts[11].isdigit() else 0
            data['卖量'] = int(parts[13]) if len(parts) > 13 and parts[13].isdigit() else 0
        
        return data
        
    except Exception as e:
        print(f"API请求失败: {e}")
        return None


def get_sina_futures_detail():
    """
    获取更详细的期货数据（使用另一个API）
    """
    try:
        # 新浪期货详情API
        url = "https://stock.finance.sina.com.cn/futures/api/json.php/Cffex_FuturesService.getCffexFuturesDailyKLine?symbol=AU0"
        
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://finance.sina.com.cn"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        # 这个API返回K线数据，我们取最新一天
        kline_data = response.json()
        
        if kline_data and len(kline_data) > 0:
            latest = kline_data[-1]
            return {
                'date': latest.get('date'),
                'open': float(latest.get('open', 0)),
                'high': float(latest.get('high', 0)),
                'low': float(latest.get('low', 0)),
                'close': float(latest.get('close', 0)),  # 收盘价即最新指数
                'volume': int(latest.get('volume', 0)),
            }
            
    except Exception as e:
        print(f"K线API失败: {e}")
        return None


def send_to_feishu(data):
    """
    发送数据到飞书
    """
    webhook_url = os.environ.get("FEISHU_WEBHOOK_URL")
    if not webhook_url:
        print("错误: 未设置 FEISHU_WEBHOOK_URL")
        return False
    
    # 判断涨跌
    change = data.get('涨跌', 0)
    trend = "📈" if change >= 0 else "📉"
    color = "green" if change >= 0 else "red"
    sign = "+" if change >= 0 else ""
    
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
                        "content": f"**💰 最新指数: {data['最新价']} 点**\n"
                                  f"**📈 涨跌: {sign}{data['涨跌']} ({sign}{data['涨跌幅']}%)**\n"
                                  f"🕐 {data['更新时间']}"
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
                                "content": f"**开盘价**\n{data['开盘价']}"
                            }
                        },
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**昨结算**\n{data['昨结算']}"
                            }
                        },
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**最高价**\n{data['最高价']}"
                            }
                        },
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**最低价**\n{data['最低价']}"
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
                                "content": f"**成交量**\n{data['成交量']:,} 手"
                            }
                        },
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**持仓量**\n{data['持仓量']:,} 手"
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
                            "content": f"📌 数据来源: 新浪财经API\n"
                                      f"⚠️ 指数基准: 1000点（2019-12-31）\n"
                                      f"🔗 https://finance.sina.com.cn/futures/quotes/AU0.shtml"
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
            print("✅ 发送成功")
            return True
        else:
            print(f"❌ 发送失败: {result}")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False


def main():
    print("=" * 60)
    print("🚀 新浪期货API - 沪金主连(AU0) 数据获取")
    print(f"⏰ {datetime.now()}")
    print("=" * 60)
    
    # 获取实时数据
    print("\n📡 正在获取实时数据...")
    data = get_sina_futures_api()
    
    if not data:
        print("❌ 获取失败，尝试备用API...")
        # 可以尝试其他API或退出
        exit(1)
    
    # 打印数据
    print(f"\n✅ 获取成功!")
    print(f"📊 品种: {data['name']}")
    print(f"💰 最新指数: {data['最新价']} 点")
    print(f"📈 涨跌: {data['涨跌']} ({data['涨跌幅']}%)")
    print(f"⬆️ 最高: {data['最高价']}  ⬇️ 最低: {data['最低价']}")
    print(f"📊 成交: {data['成交量']:,}手  持仓: {data['持仓量']:,}手")
    print(f"🕐 时间: {data['更新时间']}")
    
    # 发送到飞书
    print(f"\n📤 正在发送到飞书...")
    if send_to_feishu(data):
        print("✅ 任务完成")
    else:
        print("❌ 任务失败")
        exit(1)


if __name__ == "__main__":
    main()
