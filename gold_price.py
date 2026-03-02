#!/usr/bin/env python3
"""
AkShare - 黄金数据获取 (上海黄金交易所 Au99.99 实时行情)
带详细调试信息
"""

import os
import sys
import json
import traceback
from datetime import datetime

import akshare as ak
import pandas as pd
import requests


def get_gold_data_sge():
    """
    使用akshare获取上海黄金交易所Au99.99实时行情
    """
    try:
        print(f"🌐 正在获取上海黄金交易所Au99.99实时行情...")
        
        # 获取SGE实时行情数据
        df = ak.spot_quotations_sge(symbol="Au99.99")
        
        print(f"✅ 数据获取成功")
        print(f"📊 数据类型: {type(df)}")
        print(f"📊 数据形状: {df.shape}")
        
        if df is None or df.empty:
            print("❌ 返回数据为空")
            return None
        
        # 打印原始数据用于调试
        print(f"\n📋 原始数据预览:")
        print(df.head().to_string())
        print(f"\n📋 数据列: {list(df.columns)}")
        
        # 获取最新一条数据(最后一行)
        latest = df.iloc[-1]
        
        print(f"\n📋 最新数据行:")
        print(latest)
        
        # 解析数据 - 根据akshare文档，列名应该是: 品种, 时间, 现价, 更新时间
        data = {
            'name': 'Au99.99(上海金)',
            '最新价': float(latest.get('现价', 0)) if pd.notna(latest.get('现价')) else 0,
            '开盘价': 0,  # 实时行情接口没有开盘价，需要从历史数据获取
            '最高价': 0,
            '最低价': 0,
            '昨收': 0,
            '涨跌额': 0,  # 实时接口没有涨跌幅，需要计算
            '涨跌幅': 0,
            '成交量': 0,  # 实时接口没有成交量
            '持仓量': 0,
            '买价': float(latest.get('现价', 0)) if pd.notna(latest.get('现价')) else 0,
            '卖价': float(latest.get('现价', 0)) if pd.notna(latest.get('现价')) else 0,
            '更新时间': f"{latest.get('更新时间', '')} {latest.get('时间', '')}",
        }
        
        # 尝试获取历史数据来计算涨跌幅
        try:
            print("\n🌐 获取历史数据计算涨跌幅...")
            hist_df = ak.spot_hist_sge(symbol='Au99.99')
            if not hist_df.empty and len(hist_df) >= 2:
                # 获取昨日收盘价
                yesterday_close = float(hist_df.iloc[-1]['close'])
                data['昨收'] = yesterday_close
                data['开盘价'] = float(hist_df.iloc[-1]['open'])
                data['最高价'] = float(hist_df.iloc[-1]['high'])
                data['最低价'] = float(hist_df.iloc[-1]['low'])
                
                # 计算涨跌
                if yesterday_close > 0:
                    data['涨跌额'] = round(data['最新价'] - yesterday_close, 2)
                    data['涨跌幅'] = round((data['涨跌额'] / yesterday_close) * 100, 2)
                
                print(f"✅ 历史数据获取成功，昨收: {yesterday_close}")
        except Exception as e:
            print(f"⚠️ 获取历史数据失败: {e}")
        
        print(f"\n✅ 解析成功:")
        print(f"   名称: {data['name']}")
        print(f"   最新价: {data['最新价']}")
        print(f"   涨跌额: {data['涨跌额']}")
        print(f"   涨跌幅: {data['涨跌幅']}%")
        print(f"   更新时间: {data['更新时间']}")
        
        return data
        
    except Exception as e:
        print(f"❌ 异常: {e}")
        print(f"📜 堆栈: {traceback.format_exc()}")
        return None


def get_gold_futures_data():
    """
    备用方案: 使用上期所黄金期货主力合约
    """
    try:
        print(f"🌐 尝试获取上期所黄金期货主力合约...")
        
        # 获取期货实时行情
        df = ak.futures_zh_realtime(symbol="沪金")
        
        print(f"✅ 期货数据获取成功")
        print(f"📊 数据形状: {df.shape}")
        print(f"\n📋 数据列: {list(df.columns)}")
        print(f"\n📋 原始数据:")
        print(df.to_string())
        
        if df is None or df.empty:
            return None
        
        # 获取主力合约(通常是第一行，连续合约)
        # 筛选出连续合约(合约代码通常包含"0")
        main_contract = df[df['symbol'].str.contains('0', na=False)]
        
        if main_contract.empty:
            main_contract = df  # 如果没有连续合约，取全部
            
        row = main_contract.iloc[0]
        
        print(f"\n📋 使用合约数据:")
        print(row)
        
        # 解析期货数据
        data = {
            'name': str(row.get('name', '沪金主力')),
            '最新价': float(row.get('trade', 0)) if pd.notna(row.get('trade')) else 0,
            '开盘价': float(row.get('open', 0)) if pd.notna(row.get('open')) else 0,
            '最高价': float(row.get('high', 0)) if pd.notna(row.get('high')) else 0,
            '最低价': float(row.get('low', 0)) if pd.notna(row.get('low')) else 0,
            '昨收': float(row.get('prevsettlement', 0)) if pd.notna(row.get('prevsettlement')) else 0,
            '昨结算': float(row.get('prevsettlement', 0)) if pd.notna(row.get('prevsettlement')) else 0,
            '涨跌额': float(row.get('change', 0)) if pd.notna(row.get('change')) else 0,
            '涨跌幅': float(row.get('changepercent', 0)) * 100 if pd.notna(row.get('changepercent')) else 0,
            '成交量': int(row.get('volume', 0)) if pd.notna(row.get('volume')) else 0,
            '持仓量': int(row.get('position', 0)) if pd.notna(row.get('position')) else 0,
            '买价': float(row.get('bid', 0)) if pd.notna(row.get('bid')) else 0,
            '卖价': float(row.get('ask', 0)) if pd.notna(row.get('ask')) else 0,
            '更新时间': str(row.get('time', datetime.now().strftime("%H:%M:%S"))),
        }
        
        # 如果涨跌幅是0但涨跌额和昨结算都有值，重新计算
        if data['涨跌幅'] == 0 and data['昨结算'] > 0 and data['涨跌额'] != 0:
            data['涨跌幅'] = round((data['涨跌额'] / data['昨结算']) * 100, 2)
        
        print(f"\n✅ 期货数据解析成功:")
        print(f"   名称: {data['name']}")
        print(f"   最新价: {data['最新价']}")
        print(f"   涨跌额: {data['涨跌额']}")
        print(f"   涨跌幅: {data['涨跌幅']}%")
        
        return data
        
    except Exception as e:
        print(f"❌ 期货数据获取失败: {e}")
        print(f"📜 堆栈: {traceback.format_exc()}")
        return None


def get_gold_data():
    """
    主函数: 获取黄金数据，优先使用SGE现货，失败则使用期货
    """
    # 首先尝试获取SGE现货数据
    data = get_gold_data_sge()
    
    # 如果现货数据获取失败或价格无效，使用期货数据
    if not data or data.get('最新价', 0) == 0:
        print("\n⚠️ 现货数据无效，切换到期货数据...")
        data = get_gold_futures_data()
    
    return data


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
        change = data.get('涨跌额', 0)
        trend = "📈" if change >= 0 else "📉"
        color = "green" if change >= 0 else "red"
        sign = "+" if change >= 0 else ""
        
        # 根据数据来源决定单位
        unit = "元/克" if "SGE" in data.get('name', '') or "Au99.99" in data.get('name', '') else "元/千克"
        volume_unit = "手" if "期货" in data.get('name', '') or "主力" in data.get('name', '') else "千克"
        
        card_message = {
            "msg_type": "interactive",
            "card": {
                "config": {"wide_screen_mode": True},
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": f"{trend} {data.get('name', '黄金')} 行情"
                    },
                    "template": color
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"**💰 最新价格: {data.get('最新价', '--')} {unit}**\n"
                                      f"**📈 涨跌: {sign}{data.get('涨跌额', '--')} ({sign}{data.get('涨跌幅', '--')}%)\n"
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
                                    "content": f"**昨结算/昨收**\n{data.get('昨结算', data.get('昨收', '--'))}"
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
                                    "content": f"**成交量**\n{data.get('成交量', '--'):,} {volume_unit}"
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
                                "content": f"📌 数据来源: AkShare(akshare.xyz)\n"
                                          f"⚠️ 数据延迟仅供参考，投资有风险"
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
    print("🚀 AkShare 黄金数据获取 - 调试模式")
    print(f"⏰ {datetime.now()}")
    print(f"🐍 Python: {sys.version}")
    print("=" * 60)
    
    # 获取数据
    print("\n" + "="*60)
    print("📡 步骤1: 获取数据")
    print("="*60)
    
    data = get_gold_data()
    
    if not data:
        print("\n❌ 获取数据失败，退出")
        sys.exit(1)
    
    # 打印最终数据
    print("\n📋 最终数据:")
    for k, v in data.items():
        print(f"   {k}: {v}")
    
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
