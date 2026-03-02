#!/usr/bin/env python3
"""
AkShare - 黄金数据获取 (适配 GitHub Actions 网络环境)
"""

import os
import sys
import json
import time
import random
import traceback
from datetime import datetime

import akshare as ak
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# 配置 requests 重试策略（针对 GitHub Actions 网络不稳定）
def create_session():
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,  # 指数退避
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    
    # 设置更长的超时（GitHub Actions 可能需要更长时间）
    session.timeout = 30
    
    # 设置国内 DNS 和 Headers 模拟国内用户
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    })
    
    return session


def get_gold_futures_realtime():
    """
    获取上期所黄金期货实时行情，带重试机制
    """
    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"🌐 尝试 {attempt + 1}/{max_retries}: 获取上期所黄金期货...")
            
            # 添加随机延迟，避免被识别为机器人
            if attempt > 0:
                sleep_time = random.uniform(2, 5)
                print(f"   等待 {sleep_time:.1f} 秒后重试...")
                time.sleep(sleep_time)
            
            # 方法1: 使用品种名称"黄金"
            df = ak.futures_zh_realtime(symbol="黄金")
            
            if df is None or df.empty:
                print("   ⚠️ 返回数据为空")
                continue
            
            print(f"   ✅ 成功获取 {len(df)} 条数据")
            
            # 查找主力连续合约
            main_contract = None
            for idx, row in df.iterrows():
                symbol = str(row.get('symbol', ''))
                if 'AU0' in symbol or '连续' in symbol:
                    main_contract = row
                    print(f"   ✅ 找到主力合约: {symbol}")
                    break
            
            # 如果没找到连续合约，找成交量最大的
            if main_contract is None:
                df_sorted = df.sort_values('volume', ascending=False)
                main_contract = df_sorted.iloc[0]
                print(f"   ⚠️ 使用成交量最大合约: {main_contract.get('symbol')}")
            
            # 解析数据
            data = {
                'name': str(main_contract.get('name', '沪金')),
                'symbol': str(main_contract.get('symbol', '')),
                '最新价': float(main_contract.get('trade', 0)) if pd.notna(main_contract.get('trade')) else 0,
                '开盘价': float(main_contract.get('open', 0)) if pd.notna(main_contract.get('open')) else 0,
                '最高价': float(main_contract.get('high', 0)) if pd.notna(main_contract.get('high')) else 0,
                '最低价': float(main_contract.get('low', 0)) if pd.notna(main_contract.get('low')) else 0,
                '昨结算': float(main_contract.get('prevsettlement', 0)) if pd.notna(main_contract.get('prevsettlement')) else 0,
                '涨跌额': float(main_contract.get('change', 0)) if pd.notna(main_contract.get('change')) else 0,
                '涨跌幅': float(main_contract.get('changepercent', 0)) if pd.notna(main_contract.get('changepercent')) else 0,
                '成交量': int(main_contract.get('volume', 0)) if pd.notna(main_contract.get('volume')) else 0,
                '持仓量': int(main_contract.get('position', 0)) if pd.notna(main_contract.get('position')) else 0,
                '买价': float(main_contract.get('bid', 0)) if pd.notna(main_contract.get('bid')) else 0,
                '卖价': float(main_contract.get('ask', 0)) if pd.notna(main_contract.get('ask')) else 0,
                '更新时间': str(main_contract.get('ticktime', datetime.now().strftime("%H:%M:%S"))),
                '日期': str(main_contract.get('tradedate', datetime.now().strftime("%Y-%m-%d"))),
            }
            
            # 重新计算涨跌幅
            if data['涨跌幅'] == 0 and data['昨结算'] > 0 and data['涨跌额'] != 0:
                data['涨跌幅'] = round((data['涨跌额'] / data['昨结算']) * 100, 2)
            
            if data['最新价'] > 0:
                print(f"   ✅ 解析成功: {data['name']} @ {data['最新价']}")
                return data
            else:
                print("   ⚠️ 价格无效，继续重试...")
                
        except Exception as e:
            print(f"   ❌ 失败: {str(e)[:100]}")
            if attempt == max_retries - 1:
                print(f"   📜 错误详情: {traceback.format_exc()[:500]}")
    
    return None


def get_gold_futures_daily():
    """
    备用方案: 使用新浪期货历史数据（更稳定，但延迟一天）
    """
    try:
        print(f"\n🌐 备用方案: 获取新浪期货历史数据...")
        
        # 使用新浪期货接口获取主力连续合约
        df = ak.futures_zh_daily_sina(symbol="AU0")
        
        if df is None or df.empty:
            return None
        
        latest = df.iloc[-1]
        
        data = {
            'name': '沪金主力(AU0)',
            'symbol': 'AU0',
            '最新价': float(latest.get('close', 0)),
            '开盘价': float(latest.get('open', 0)),
            '最高价': float(latest.get('high', 0)),
            '最低价': float(latest.get('low', 0)),
            '昨结算': float(latest.get('close', 0)),
            '涨跌额': 0,
            '涨跌幅': 0,
            '成交量': int(latest.get('volume', 0)),
            '持仓量': int(latest.get('hold', 0)) if 'hold' in latest else 0,
            '买价': float(latest.get('close', 0)),
            '卖价': float(latest.get('close', 0)),
            '更新时间': str(latest.get('date', datetime.now().strftime("%Y-%m-%d"))),
            '日期': str(latest.get('date', datetime.now().strftime("%Y-%m-%d"))),
            'data_source': '新浪期货(历史)',
        }
        
        # 计算涨跌
        if len(df) >= 2:
            prev_close = float(df.iloc[-2]['close'])
            data['昨结算'] = prev_close
            data['涨跌额'] = round(data['最新价'] - prev_close, 2)
            data['涨跌幅'] = round((data['涨跌额'] / prev_close) * 100, 2) if prev_close > 0 else 0
        
        print(f"   ✅ 历史数据获取成功: {data['最新价']}")
        return data
        
    except Exception as e:
        print(f"   ❌ 备用方案失败: {e}")
        return None


def get_gold_data():
    """
    主函数: 带完整降级策略
    """
    # 方案1: 实时行情（可能因网络问题失败）
    data = get_gold_futures_realtime()
    
    # 方案2: 历史数据（更稳定）
    if not data or data.get('最新价', 0) == 0:
        print("\n⚠️ 实时行情失败，切换到历史数据...")
        data = get_gold_futures_daily()
    
    # 方案3: 使用静态数据或缓存（最后手段）
    if not data:
        print("\n❌ 所有数据源均失败")
        # 可以在这里添加从缓存文件读取的逻辑
        
    return data

def send_wechat(self, data):
        """
        发送到企业微信机器人
        文档: https://developer.work.weixin.qq.com/document/path/91770
        """
        print("\n📤 发送到企业微信...")
        
        webhook_url = os.environ.get("WECHAT_WEBHOOK_URL")
        if not webhook_url:
            print("❌ 未配置 WECHAT_WEBHOOK_URL")
            return False
        
        try:
            content, trend, sign, is_trading = self._build_message_content(data)
            change = data.get('涨跌额', 0)
            
            # 企业微信支持多种消息类型：text, markdown, image, news等
            # 这里使用 markdown 类型，格式丰富且手机端显示友好
            
            markdown_content = f"""## {content['title']}

> 💰 **最新价格**: {content['price']}
> 📈 **涨跌**: {content['change']}
> 🕐 **时间**: {content['time']}
> 📊 **市场状态**: {content['market_status']}

**详细数据**:
- 开盘价: {content['open']}
- 最高价: {content['high']}
- 最低价: {content['low']}
- 昨结算: {data.get('昨结算', '--')}
- 成交量: {content['volume']}
- 持仓量: {content['position']}

---
📌 数据来源: {content['source']}
⚠️ 仅供参考，投资有风险
"""
            
            # 如果涨跌幅度大，添加提醒
            if abs(data.get('涨跌幅', 0)) > 2:
                markdown_content = f"## ⚠️ 波动提醒\n\n{markdown_content}"
            
            message = {
                "msgtype": "markdown",
                "markdown": {
                    "content": markdown_content
                }
            }
            
            response = requests.post(
                webhook_url,
                headers={"Content-Type": "application/json"},
                json=message,
                timeout=10
            )
            
            result = response.json()
            
            # 企业微信返回格式: {"errcode": 0, "errmsg": "ok"}
            if result.get("errcode") == 0:
                print("✅ 企业微信发送成功")
                return True
            else:
                print(f"❌ 企业微信返回错误: {result}")
                return False
                
        except Exception as e:
            print(f"❌ 企业微信发送异常: {e}")
            return False

def send_to_feishu(data):
    """
    发送数据到飞书
    """
    webhook_url = os.environ.get("FEISHU_WEBHOOK_URL")
    
    print(f"\n📤 准备发送飞书...")
    
    if not webhook_url:
        print("❌ 错误: 未设置 FEISHU_WEBHOOK_URL 环境变量")
        return False
    
    try:
        change = data.get('涨跌额', 0)
        trend = "📈" if change >= 0 else "📉"
        color = "green" if change >= 0 else "red"
        sign = "+" if change >= 0 else ""
        
        # 判断数据来源
        is_realtime = 'ticktime' in str(data.get('更新时间', ''))
        data_source = "实时" if is_realtime else data.get('data_source', '历史')
        
        unit = "元/克"
        
        card_message = {
            "msg_type": "interactive",
            "card": {
                "config": {"wide_screen_mode": True},
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": f"{trend} {data.get('name', '沪金')} 行情 ({data_source})"
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
                                "content": f"📌 数据来源: AkShare\n"
                                          f"🔧 运行环境: {'GitHub Actions' if os.environ.get('GITHUB_ACTIONS') else '本地'}\n"
                                          f"⚠️ 仅供参考，投资有风险"
                            }
                        ]
                    }
                ]
            }
        }
        
        response = requests.post(
            webhook_url,
            headers={"Content-Type": "application/json"},
            json=card_message,
            timeout=10
        )
        
        result = response.json()
        
        if result.get("code") == 0:
            print("✅ 飞书发送成功")
            return True
        else:
            print(f"❌ 飞书返回错误: {result}")
            return False
            
    except Exception as e:
        print(f"❌ 发送异常: {e}")
        return False


def main():
    print("=" * 60)
    print("🚀 AkShare 黄金数据获取 - GitHub Actions 适配版")
    print(f"⏰ {datetime.now()}")
    print(f"🐍 Python: {sys.version}")
    print(f"🔧 环境: {'GitHub Actions' if os.environ.get('GITHUB_ACTIONS') else '本地'}")
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

    # 发送企业微信
    send_wechat(data)
    
    if not success:
        print("\n❌ 发送失败，退出")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("✅ 全部完成")
    print("="*60)
https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=59f43ddf-11ac-4ea8-8f00-2e8bf7737226

if __name__ == "__main__":
    main()
