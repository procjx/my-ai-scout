#!/usr/bin/env python3
"""
新浪期货API - 沪金主连(AU0) 数据获取
带详细调试信息
"""

import os
import sys
import json
import requests
import traceback
from datetime import datetime


def get_sina_futures_api():
    """
    使用新浪期货API获取数据
    """
    url = "https://hq.sinajs.cn/list=AU0"
    
    headers = {
        "Referer": "https://finance.sina.com.cn",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "*/*",
        "Accept-Language": "zh-CN,zh;q=0.9",
    }
    
    try:
        print(f"🌐 请求URL: {url}")
        response = requests.get(url, headers=headers, timeout=15)
        
        print(f"📊 状态码: {response.status_code}")
        print(f"📋 编码: {response.encoding}")
        print(f"📏 内容长度: {len(response.text)}")
        
        # 尝试多种编码
        for encoding in ['gb2312', 'gbk', 'utf-8']:
            try:
                response.encoding = encoding
                text = response.text
                print(f"\n🔤 尝试编码 {encoding}: {text[:100]}...")
                break
            except Exception as e:
                print(f"   {encoding}失败: {e}")
                continue
        
        # 检查返回内容
        if not text or len(text) < 50:
            print("❌ 返回内容太短:", repr(text))
            return None
        
        # 提取数据
        if 'hq_str_AU0=' not in text:
            print("❌ 未找到 hq_str_AU0 标识")
            print("返回内容:", text[:500])
            return None
        
        # 提取引号内容
        try:
            data_str = text.split('"')[1]
            print(f"✅ 提取数据字符串: {data_str[:100]}...")
        except IndexError as e:
            print(f"❌ 分割引号失败: {e}")
            print("完整内容:", text)
            return None
        
        parts = data_str.split(',')
        print(f"✅ 分割字段数: {len(parts)}")
        
        if len(parts) < 10:
            print(f"❌ 字段数不足: {parts}")
            return None
        
        # 打印前10个字段用于调试
        print("\n📋 字段预览:")
        for i, p in enumerate(parts[:10]):
            print(f"   [{i}] {p}")
        
        # 解析数据
        data = {
            'name': parts[0],
            '开盘价': float(parts[1]) if parts[1].replace('.','').isdigit() else 0,
            '昨结算': float(parts[2]) if parts[2].replace('.','').isdigit() else 0,
            '最新价': float(parts[3]) if parts[3].replace('.','').isdigit() else 0,
            '最高价': float(parts[4]) if parts[4].replace('.','').isdigit() else 0,
            '最低价': float(parts[5]) if parts[5].replace('.','').isdigit() else 0,
            '买价': float(parts[6]) if parts[6].replace('.','').isdigit() else 0,
            '卖价': float(parts[7]) if parts[7].replace('.','').isdigit() else 0,
            '成交量': int(parts[8]) if parts[8].isdigit() else 0,
            '持仓量': int(parts[9]) if parts[9].isdigit() else 0,
        }
        
        # 时间通常在最后
        if len(parts) >= 3:
            data['更新时间'] = f"{parts[-3]} {parts[-2]}" if len(parts) >= 2 else "未知"
        else:
            data['更新时间'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 计算涨跌
        data['涨跌'] = round(data['最新价'] - data['昨结算'], 3)
        data['涨跌幅'] = round((data['涨跌'] / data['昨结算']) * 100, 2) if data['昨结算'] > 0 else 0
        
        print(f"\n✅ 解析成功:")
        print(f"   名称: {data['name']}")
        print(f"   最新价: {data['最新价']}")
        print(f"   涨跌: {data['涨跌']}")
        
        return data
        
    except Exception as e:
        print(f"❌ 异常: {e}")
        print(f"📜 堆栈: {traceback.format_exc()}")
        return None


def send_to_feishu(data):
    """
    发送数据到飞书
    """
    webhook_url = os.environ.get("FEISHU_WEBHOOK_URL")
    
    print(f"\n📤 准备发送飞书...")
    print(f"   Webhook存在: {'是' if webhook_url else '否'}")
    
    if not webhook_url:
        print("❌ 错误: 未设置 FEISHU_WEBHOOK_URL 环境变量")
        return False
    
    # 隐藏部分URL用于安全显示
    safe_url = webhook_url[:50] + "..." if len(webhook_url) > 50 else webhook_url
    print(f"   URL: {safe_url}")
    
    try:
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
                            "content": f"**💰 最新指数: {data.get('最新价', '--')} 点**\n"
                                      f"**📈 涨跌: {sign}{data.get('涨跌', '--')} ({sign}{data.get('涨跌幅', '--')}%)**\n"
                                      f"🕐 {data.get('更新时间', '--')}"
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
                                    "content": f"**开盘价**\n{data.get('开盘价', '--')}"
                                }
                            },
                            {
                                "is_short": True,
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**昨结算**\n{data.get('昨结算', '--')}"
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
                                    "content": f"**成交量**\n{data.get('成交量', '--'):,} 手"
                                }
                            },
                            {
                                "is_short": True,
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**持仓量**\n{data.get('持仓量', '--'):,} 手"
                                }
                            }
                        ]
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
                                          f"⚠️ 指数基准: 1000点（2019-12-31）"
                            }
                        ]
                    }
                ]
            }
        }
        
        print(f"   发送请求...")
        response = requests.post(
            webhook_url,
            headers={"Content-Type": "application/json"},
            json=card_message,
            timeout=10
        )
        
        print(f"   状态码: {response.status_code}")
        print(f"   返回: {response.text[:200]}")
        
        result = response.json()
        
        if result.get("code") == 0:
            print("✅ 飞书发送成功")
            return True
        else:
            print(f"❌ 飞书返回错误: {result}")
            return False
            
    except Exception as e:
        print(f"❌ 发送异常: {e}")
        print(f"📜 堆栈: {traceback.format_exc()}")
        return False


def main():
    print("=" * 60)
    print("🚀 新浪期货API - 调试模式")
    print(f"⏰ {datetime.now()}")
    print(f"🐍 Python: {sys.version}")
    print("=" * 60)
    
    # 获取数据
    print("\n" + "="*60)
    print("📡 步骤1: 获取数据")
    print("="*60)
    
    data = get_sina_futures_api()
    
    if not data:
        print("\n❌ 获取数据失败，退出")
        sys.exit(1)
    
    # 发送飞书
    print("\n" + "="*60)
    print("📤 步骤2: 发送飞书")
    print("="*60)
    
    success = send_to_feishu(data)
    
    if not success:
        print("\n❌ 发送失败，退出")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("✅ 全部完成")
    print("="*60)


if __name__ == "__main__":
    main()
