#!/usr/bin/env python3
"""
A股选股系统 - Streamlit Web界面
"""

import streamlit as st
import sys
import os
import time
import pandas as pd
from typing import Dict, List, Any, Optional
import json
from datetime import datetime
import traceback

# 添加项目路径
project_root = os.path.dirname(__file__)
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, project_root)
sys.path.insert(0, src_path)

# 配置页面
st.set_page_config(
    page_title="A股选股系统",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS样式
st.markdown("""
<style>
.main > div {
    padding-top: 2rem;
}

.stAlert {
    margin-top: 1rem;
    margin-bottom: 1rem;
}

.metric-card {
    background-color: #f0f2f6;
    border-radius: 10px;
    padding: 1rem;
    margin: 0.5rem 0;
}

.success-metric {
    background-color: #d4edda;
    color: #155724;
}

.warning-metric {
    background-color: #fff3cd;
    color: #856404;
}

.error-metric {
    background-color: #f8d7da;
    color: #721c24;
}

.stock-card {
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 1rem;
    margin: 0.5rem 0;
    background-color: white;
}

.rule-result {
    display: inline-block;
    padding: 0.2rem 0.5rem;
    border-radius: 15px;
    font-size: 0.8rem;
    margin: 0.2rem;
}

.rule-pass {
    background-color: #d4edda;
    color: #155724;
}

.rule-fail {
    background-color: #f8d7da;
    color: #721c24;
}

.rule-partial {
    background-color: #fff3cd;
    color: #856404;
}
</style>
""", unsafe_allow_html=True)

class StockSelectionApp:
    """股票选择应用主类"""
    
    def __init__(self):
        self.init_session_state()
        
    def init_session_state(self):
        """初始化会话状态"""
        if 'scan_results' not in st.session_state:
            st.session_state.scan_results = None
        if 'scan_running' not in st.session_state:
            st.session_state.scan_running = False
        if 'scan_progress' not in st.session_state:
            st.session_state.scan_progress = {'current': 0, 'total': 0, 'found': 0}
        if 'selector' not in st.session_state:
            st.session_state.selector = None
        if 'last_scan_time' not in st.session_state:
            st.session_state.last_scan_time = None
    
    def render_header(self):
        """渲染页面头部"""
        st.title("📈 A股选股系统")
        st.markdown("---")
        
        # 系统状态指示器
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.session_state.selector:
                st.metric("系统状态", "✅ 已就绪", delta="引擎加载完成")
            else:
                st.metric("系统状态", "⏳ 初始化中", delta="正在加载...")
        
        with col2:
            if st.session_state.last_scan_time:
                time_diff = datetime.now() - st.session_state.last_scan_time
                
                # 计算时间差
                total_seconds = int(time_diff.total_seconds())
                days = total_seconds // 86400
                hours = (total_seconds % 86400) // 3600
                minutes = (total_seconds % 3600) // 60
                
                if days > 0:
                    time_str = f"{days}天前"
                elif hours > 0:
                    time_str = f"{hours}小时前"
                elif minutes > 0:
                    time_str = f"{minutes}分钟前"
                else:
                    time_str = "刚刚"
                    
                st.metric("上次扫描", time_str, delta="扫描历史")
            else:
                st.metric("上次扫描", "无", delta="首次使用")
        
        with col3:
            if st.session_state.scan_results:
                result_count = len(st.session_state.scan_results.get('results', []))
                st.metric("发现股票", f"{result_count}只", delta="符合条件")
            else:
                st.metric("发现股票", "0只", delta="等待扫描")
        
        with col4:
            if st.session_state.scan_running:
                progress = st.session_state.scan_progress
                percent = (progress['current'] / progress['total'] * 100) if progress['total'] > 0 else 0
                st.metric("扫描进度", f"{percent:.1f}%", delta="进行中")
            else:
                # 检查是否有最近的扫描结果
                if st.session_state.scan_results and st.session_state.last_scan_time:
                    st.metric("扫描进度", "完成", delta="已结束")
                else:
                    st.metric("扫描进度", "就绪", delta="待开始")
    
    def render_sidebar(self):
        """渲染侧边栏配置"""
        st.sidebar.header("⚙️ 扫描配置")
        
        # 基本参数配置
        st.sidebar.subheader("基本参数")
        
        scan_mode = st.sidebar.selectbox(
            "扫描板块",
            ["沪市主板", "深市主板", "创业板", "科创板", "全部板块"],
            help="沪市主板:600xxx | 深市主板:000xxx,002xxx | 创业板:300xxx | 科创板:688xxx | 全部板块:所有A股"
        )
        
        max_results = st.sidebar.selectbox(
            "最大结果数量",
            [10, 20, 50, 100, 200, 500],
            index=2,  # 默认50
            help="限制最终返回的符合条件股票数量（不是扫描数量）"
        )
        
        min_score = st.sidebar.slider(
            "最低评分阈值",
            min_value=0.0,
            max_value=100.0,
            value=60.0,
            step=5.0,
            help="只显示评分高于此阈值的股票"
        )
        
        # 规则配置
        st.sidebar.subheader("选股规则")
        
        use_golden_pit = st.sidebar.checkbox(
            "黄金坑规则",
            value=True,
            help="检测深度回调后重新站上均线的机会（简化版）"
        )
        
        use_trend_breakout = st.sidebar.checkbox(
            "趋势突破规则（升级版）",
            value=True,
            help="多头趋势中连续倍量大震幅突破8个月高点（升级版）"
        )
        
        # 高级配置
        st.sidebar.subheader("高级设置")
        
        max_workers = st.sidebar.slider(
            "并发线程数",
            min_value=1,
            max_value=10,
            value=5,
            help="增加线程数可提高扫描速度，但会增加系统负载"
        )
        
        save_results = st.sidebar.checkbox(
            "保存扫描结果",
            value=True,
            help="自动保存扫描结果到文件"
        )
        
        export_format = st.sidebar.selectbox(
            "导出格式",
            ["CSV", "JSON", "Excel"],
            help="选择结果导出格式"
        )
        
        return {
            'scan_mode': scan_mode,
            'max_results': max_results,
            'min_score': min_score,
            'use_golden_pit': use_golden_pit,
            'use_trend_breakout': use_trend_breakout,
            'max_workers': max_workers,
            'save_results': save_results,
            'export_format': export_format
        }
    
    def initialize_selector(self):
        """初始化选股器"""
        if st.session_state.selector is None:
            try:
                with st.spinner("正在初始化选股引擎..."):
                    # 使用真实的选股器
                    try:
                        from src.real_stock_selector import RealStockSelector
                        st.session_state.selector = RealStockSelector()
                        st.session_state.is_real_selector = True
                    except ImportError as e:
                        st.warning("真实选股器初始化失败，使用模拟模式")
                        st.session_state.selector = MockStockSelector()
                        st.session_state.is_real_selector = False
                st.success("选股引擎初始化成功！")
                return True
            except Exception as e:
                st.error(f"选股引擎初始化失败: {str(e)}")
                st.error("请检查系统环境和依赖库是否正确安装")
                return False
        return True
    
    def run_stock_scan_inline(self, config, progress_bar, status_text):
        """内联扫描函数，直接更新UI"""
        if not st.session_state.selector:
            status_text.text("选股引擎未初始化")
            st.session_state.scan_running = False
            return
        
        # 根据板块确定扫描股票列表
        if config['scan_mode'] == "沪市主板":
            # 沪市主板：600xxx, 601xxx, 603xxx, 605xxx等
            symbols = []
            symbols.extend([f'6{i:05d}' for i in range(0, 10000)])  # 600000~609999
            # 过滤掉不存在的范围，保留主要的600, 601, 603, 605系列
            symbols = [s for s in symbols if s.startswith(('60000', '60001', '60002', '60003', '60004', '60005', '60006', '60007', '60008', '60009',
                                                           '60100', '60101', '60102', '60103', '60104', '60105', '60106', '60107', '60108', '60109',
                                                           '60300', '60301', '60302', '60303', '60304', '60305', '60306', '60307', '60308', '60309',
                                                           '60500', '60501', '60502', '60503', '60504', '60505', '60506', '60507', '60508', '60509'))]
            symbols = symbols[:800]  # 限制数量避免过多
            
        elif config['scan_mode'] == "深市主板":
            # 深市主板：000xxx, 002xxx
            symbols = []
            symbols.extend([f'{i:06d}' for i in range(1, 2000)])      # 000001~001999
            symbols.extend([f'{i:06d}' for i in range(2001, 4000)])   # 002001~003999
            
        elif config['scan_mode'] == "创业板":
            # 创业板：300xxx
            symbols = [f'3{i:05d}' for i in range(1, 1000)]  # 300001~300999
            
        elif config['scan_mode'] == "科创板":
            # 科创板：688xxx
            symbols = [f'688{i:03d}' for i in range(1, 1000)]  # 688001~688999
            
        else:  # 全部板块
            symbols = []
            # 沪市主板
            symbols.extend([f'6{i:05d}' for i in range(0, 1000)])     # 600000~600999 (简化)
            symbols.extend([f'6{i:05d}' for i in range(1000, 2000)])  # 601000~601999
            symbols.extend([f'6{i:05d}' for i in range(3000, 4000)])  # 603000~603999
            symbols.extend([f'6{i:05d}' for i in range(5000, 6000)])  # 605000~605999
            # 深市主板
            symbols.extend([f'{i:06d}' for i in range(1, 1000)])      # 000001~000999
            symbols.extend([f'{i:06d}' for i in range(2001, 3000)])   # 002001~002999
            # 创业板
            symbols.extend([f'3{i:05d}' for i in range(1, 500)])      # 300001~300499
            # 科创板
            symbols.extend([f'688{i:03d}' for i in range(1, 200)])    # 688001~688199
        
        # 构建规则名称列表
        rule_names = []
        if config['use_golden_pit']:
            rule_names.append('GoldenPit')
        if config['use_trend_breakout']:
            rule_names.append('TrendBreakout')
        
        if not rule_names:
            status_text.text("请至少选择一个选股规则")
            st.session_state.scan_running = False
            return
        
        try:
            # 定义进度回调函数，直接更新UI组件
            def progress_callback(current, total, found):
                """进度回调函数"""
                st.session_state.scan_progress = {
                    'current': current, 
                    'total': total, 
                    'found': found
                }
                
                # 直接更新UI组件
                progress_percent = current / total if total > 0 else 0
                progress_bar.progress(progress_percent)
                status_text.text(f"进度: {current}/{total} ({progress_percent*100:.1f}%) - 已发现 {found} 只符合条件的股票")
            
            # 执行扫描
            results = st.session_state.selector.scan_stocks_advanced(
                symbols=symbols,
                rule_names=rule_names,
                min_score=config['min_score'],
                max_workers=config['max_workers'],
                save_results=config['save_results'],
                progress_callback=progress_callback,
                max_results=config['max_results']
            )
            
            # 更新会话状态
            st.session_state.scan_results = results
            st.session_state.last_scan_time = datetime.now()
            st.session_state.scan_running = False
            st.session_state.scan_started = False  # 重置扫描状态，允许下次扫描
            
            # 显示完成信息
            progress_bar.progress(1.0)
            final_count = len(results.get('results', []))
            status_text.text(f"{config['scan_mode']}扫描完成！找到 {final_count} 只符合条件的股票")
            
            # 扫描完成后显示更新的状态摘要
            with st.container():
                st.success(f"✅ 扫描完成！共找到 {final_count} 只符合条件的股票")
                
                # 创建状态摘要
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("本次发现", f"{final_count}只", delta="符合条件")
                with col2:
                    current_time = st.session_state.last_scan_time.strftime("%H:%M:%S")
                    st.metric("完成时间", current_time, delta="刚刚")
                with col3:
                    total_scanned = len(symbols)
                    st.metric("扫描范围", f"{total_scanned}只", delta=config['scan_mode'])
            
            # 在扫描完成2秒后刷新页面以更新状态栏
            import time
            time.sleep(2)
            st.rerun()
            
        except Exception as e:
            st.session_state.scan_running = False
            st.session_state.scan_started = False
            # 只更新状态文本，不创建新的UI组件
            status_text.text(f"扫描失败: {str(e)}")
            progress_bar.progress(0)
            st.error(f"扫描过程中发生错误: {str(e)}")

    def render_results(self):
        """渲染扫描结果"""
        if not st.session_state.scan_results:
            st.info("暂无扫描结果，请先执行股票扫描")
            return
        
        results = st.session_state.scan_results.get('results', [])
        statistics = st.session_state.scan_results.get('statistics', {})
        
        st.subheader("📊 扫描结果概览")
        
        # 统计信息卡片
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div class="metric-card success-metric">
                <h3>符合条件股票</h3>
                <h2>{} 只</h2>
            </div>
            """.format(len(results)), unsafe_allow_html=True)
        
        with col2:
            total_scanned = statistics.get('total_symbols', 0)
            st.markdown("""
            <div class="metric-card">
                <h3>总扫描数量</h3>
                <h2>{} 只</h2>
            </div>
            """.format(total_scanned), unsafe_allow_html=True)
        
        with col3:
            qualification_rate = statistics.get('qualification_rate', 0)
            st.markdown("""
            <div class="metric-card warning-metric">
                <h3>通过率</h3>
                <h2>{:.1f}%</h2>
            </div>
            """.format(qualification_rate), unsafe_allow_html=True)
        
        with col4:
            processing_time = statistics.get('total_processing_time', 0)
            st.markdown("""
            <div class="metric-card">
                <h3>处理时间</h3>
                <h2>{:.1f}秒</h2>
            </div>
            """.format(processing_time), unsafe_allow_html=True)
        
        if results:
            # 结果展示选项
            st.subheader("📈 股票选择结果")
            
            # 检查启用的规则
            enabled_rules = []
            if st.session_state.get('last_scan_config', {}).get('use_golden_pit', False):
                enabled_rules.append('黄金坑规则')
            if st.session_state.get('last_scan_config', {}).get('use_trend_breakout', False):
                enabled_rules.append('趋势突破规则')
            
            if len(enabled_rules) == 1:
                # 只有一个规则时，直接显示
                rule_name = enabled_rules[0]
                self.render_single_rule_results(results, rule_name)
            else:
                # 多个规则时，分标签页显示
                rule_tabs = st.tabs(enabled_rules + ["综合视图"])
                
                for i, rule_name in enumerate(enabled_rules):
                    with rule_tabs[i]:
                        self.render_single_rule_results(results, rule_name)
                
                # 综合视图保留原有的详细显示
                with rule_tabs[-1]:
                    detail_tabs = st.tabs(["列表视图", "详细视图", "规则分析"])
                    with detail_tabs[0]:
                        self.render_list_view(results)
                    with detail_tabs[1]:
                        self.render_detailed_view(results)
                    with detail_tabs[2]:
                        self.render_rule_analysis(results)
    
    def render_list_view(self, results):
        """渲染列表视图"""
        # 创建DataFrame用于显示
        display_data = []
        for i, result in enumerate(results, 1):
            row = {
                '排名': i,
                '股票代码': result['symbol'],
                '综合评分': f"{result['composite_score']:.1f}",
            }
            
            # 添加规则结果
            for rule_result in result.get('results', []):
                rule_name = rule_result.rule_name
                rule_score = f"{rule_result.score:.1f}"
                rule_status = rule_result.result.name
                row[f'{rule_name}评分'] = rule_score
                row[f'{rule_name}状态'] = rule_status
            
            display_data.append(row)
        
        if display_data:
            df = pd.DataFrame(display_data)
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    '排名': st.column_config.NumberColumn(width="small"),
                    '股票代码': st.column_config.TextColumn(width="medium"),
                    '综合评分': st.column_config.NumberColumn(width="small"),
                }
            )
    
    def render_detailed_view(self, results):
        """渲染详细视图"""
        for i, result in enumerate(results[:20], 1):  # 只显示前20个
            with st.container():
                st.markdown(f"""
                <div class="stock-card">
                    <h4>#{i} {result['symbol']} - 综合评分: {result['composite_score']:.1f}</h4>
                </div>
                """, unsafe_allow_html=True)
                
                # 规则结果展示
                rule_cols = st.columns(len(result.get('results', [])))
                for j, rule_result in enumerate(result.get('results', [])):
                    with rule_cols[j]:
                        status_class = {
                            'PASS': 'rule-pass',
                            'FAIL': 'rule-fail', 
                            'PARTIAL': 'rule-partial'
                        }.get(rule_result.result.name, 'rule-fail')
                        
                        st.markdown(f"""
                        <div class="rule-result {status_class}">
                            <strong>{rule_result.rule_name}</strong><br>
                            评分: {rule_result.score:.1f}<br>
                            状态: {rule_result.result.name}<br>
                            置信度: {rule_result.confidence:.1f}%
                        </div>
                        """, unsafe_allow_html=True)
                
                # 详细信息
                with st.expander("查看详细信息"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**数据信息:**")
                        data_info = result.get('data_info', {})
                        st.write(f"- 数据长度: {data_info.get('data_length', 'N/A')}")
                        st.write(f"- 日期范围: {data_info.get('date_range', 'N/A')}")
                        st.write(f"- 指标数量: {data_info.get('indicators_count', 'N/A')}")
                    
                    with col2:
                        st.write("**评分详情:**")
                        score_details = result.get('score_details', {})
                        if score_details:
                            for rule_name, score in score_details.items():
                                st.write(f"- {rule_name}: {score:.1f}")
                
                st.markdown("---")
    
    def render_rule_analysis(self, results):
        """渲染规则分析"""
        if not results:
            return
        
        # 统计规则表现
        rule_stats = {}
        for result in results:
            for rule_result in result.get('results', []):
                rule_name = rule_result.rule_name
                if rule_name not in rule_stats:
                    rule_stats[rule_name] = {'pass': 0, 'fail': 0, 'partial': 0, 'error': 0, 'scores': []}
                
                rule_stats[rule_name][rule_result.result.name.lower()] += 1
                rule_stats[rule_name]['scores'].append(rule_result.score)
        
        st.subheader("规则性能分析")
        
        for rule_name, stats in rule_stats.items():
            with st.container():
                st.write(f"**{rule_name} 规则表现:**")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("通过", stats['pass'], delta="个股票")
                with col2:
                    st.metric("失败", stats['fail'], delta="个股票")
                with col3:
                    st.metric("部分通过", stats['partial'], delta="个股票")
                with col4:
                    avg_score = sum(stats['scores']) / len(stats['scores']) if stats['scores'] else 0
                    st.metric("平均评分", f"{avg_score:.1f}", delta="分")
                
                # 评分分布
                if stats['scores']:
                    score_ranges = {
                        '90-100': len([s for s in stats['scores'] if 90 <= s <= 100]),
                        '80-89': len([s for s in stats['scores'] if 80 <= s < 90]),
                        '70-79': len([s for s in stats['scores'] if 70 <= s < 80]),
                        '60-69': len([s for s in stats['scores'] if 60 <= s < 70]),
                        '< 60': len([s for s in stats['scores'] if s < 60])
                    }
                    
                    st.write("评分分布:")
                    score_df = pd.DataFrame([score_ranges]).T
                    score_df.columns = ['股票数量']
                    st.bar_chart(score_df)
                
                st.markdown("---")
    
    def render_single_rule_results(self, results, rule_name):
        """渲染单个规则的专属结果展示"""
        # 根据规则名称确定规则键
        rule_key = 'GoldenPit' if rule_name == '黄金坑规则' else 'TrendBreakout'
        
        # 筛选包含该规则结果的股票
        filtered_results = []
        for result in results:
            # 检查该股票是否有这个规则的数据
            if rule_key in result.get('rule_data', {}):
                # 检查该规则是否通过
                rule_passed = any(r.rule_name == rule_key and r.result.name in ['PASS', 'PARTIAL'] 
                                for r in result.get('results', []))
                if rule_passed:
                    filtered_results.append(result)
        
        if not filtered_results:
            st.info(f"暂无符合{rule_name}条件的股票")
            return
            
        st.write(f"**{rule_name}筛选结果：**")
        
        if rule_name == '黄金坑规则':
            self.render_golden_pit_table(filtered_results)
        else:
            self.render_trend_breakout_table(filtered_results)
    
    def render_golden_pit_table(self, results):
        """渲染黄金坑规则专属表格"""
        display_data = []
        
        for result in results:
            rule_data = result.get('rule_data', {}).get('GoldenPit', {})
            
            row = {
                '股票代码': result['symbol'],
                '股票名称': result.get('stock_name', '未知'),
                '当前价格': rule_data.get('current_price', 0),
                '触发日期': rule_data.get('trigger_date', ''),
                '前期高点': rule_data.get('previous_high', 0),
                '最大跌幅': rule_data.get('max_drawdown', ''),
                '突破幅度': rule_data.get('breakout_margin', ''),
                '10日均线': rule_data.get('ma10', 0)
            }
            display_data.append(row)
        
        if display_data:
            df = pd.DataFrame(display_data)
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    '股票代码': st.column_config.TextColumn(width="medium"),
                    '股票名称': st.column_config.TextColumn(width="medium"),
                    '当前价格': st.column_config.NumberColumn(width="small", format="%.2f"),
                    '触发日期': st.column_config.TextColumn(width="medium"),
                    '前期高点': st.column_config.NumberColumn(width="small", format="%.2f"),
                    '最大跌幅': st.column_config.TextColumn(width="small"),
                    '突破幅度': st.column_config.TextColumn(width="small"),
                    '10日均线': st.column_config.NumberColumn(width="small", format="%.2f")
                }
            )
    
    def render_trend_breakout_table(self, results):
        """渲染趋势突破规则专属表格"""
        display_data = []
        
        for result in results:
            rule_data = result.get('rule_data', {}).get('TrendBreakout', {})
            
            row = {
                '股票代码': result['symbol'],
                '股票名称': result.get('stock_name', '未知'),
                '当前价格': rule_data.get('current_price', 0),
                '触发日期': rule_data.get('trigger_date', ''),
                '前期高点': rule_data.get('previous_high', 0),
                '突破幅度': rule_data.get('breakout_margin', ''),
                '连续放量天数': rule_data.get('volume_days', ''),
                '平均量比': rule_data.get('avg_volume_ratio', 0)
            }
            display_data.append(row)
        
        if display_data:
            df = pd.DataFrame(display_data)
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    '股票代码': st.column_config.TextColumn(width="medium"),
                    '股票名称': st.column_config.TextColumn(width="medium"),
                    '当前价格': st.column_config.NumberColumn(width="small", format="%.2f"),
                    '触发日期': st.column_config.TextColumn(width="medium"),
                    '前期高点': st.column_config.NumberColumn(width="small", format="%.2f"),
                    '突破幅度': st.column_config.TextColumn(width="small"),
                    '连续放量天数': st.column_config.TextColumn(width="small"),
                    '平均量比': st.column_config.NumberColumn(width="small", format="%.2f")
                }
            )
    
    def render_export_section(self):
        """渲染结果导出区域"""
        if not st.session_state.scan_results:
            return
        
        st.subheader("📥 结果导出")
        
        # 导出模式选择
        export_mode = st.selectbox(
            "导出模式",
            ["综合结果导出", "黄金坑规则结果", "趋势突破规则结果"],
            help="选择要导出的结果类型"
        )
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("导出CSV", use_container_width=True):
                try:
                    # 根据导出模式生成文件名
                    mode_suffix = {
                        "综合结果导出": "comprehensive",
                        "黄金坑规则结果": "golden_pit",
                        "趋势突破规则结果": "trend_breakout"
                    }.get(export_mode, "comprehensive")
                    
                    filename = f"stock_selection_{mode_suffix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                    st.success(f"CSV文件已导出: {filename}")
                    st.info(f"导出模式: {export_mode}")
                except Exception as e:
                    st.error(f"导出失败: {str(e)}")
        
        with col2:
            if st.button("导出JSON", use_container_width=True):
                try:
                    # 根据导出模式生成文件名
                    mode_suffix = {
                        "综合结果导出": "comprehensive",
                        "黄金坑规则结果": "golden_pit",
                        "趋势突破规则结果": "trend_breakout"
                    }.get(export_mode, "comprehensive")
                    
                    filename = f"stock_selection_{mode_suffix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    st.success(f"JSON文件已导出: {filename}")
                    st.info(f"导出模式: {export_mode}")
                except Exception as e:
                    st.error(f"导出失败: {str(e)}")
        
        with col3:
            if st.button("查看历史记录", use_container_width=True):
                self.show_history_modal()
    
    def show_history_modal(self):
        """显示历史记录模态框"""
        with st.container():
            st.subheader("📚 扫描历史记录")
            
            # 模拟历史记录
            history_data = [
                {
                    'scan_id': '20240826_103045',
                    'timestamp': '2024-08-26 10:30:45',
                    'qualified_stocks': 15,
                    'total_scanned': 100,
                    'qualification_rate': 15.0,
                    'processing_time': 45.2
                },
                {
                    'scan_id': '20240825_154320',
                    'timestamp': '2024-08-25 15:43:20',
                    'qualified_stocks': 23,
                    'total_scanned': 200,
                    'qualification_rate': 11.5,
                    'processing_time': 89.1
                }
            ]
            
            if history_data:
                df = pd.DataFrame(history_data)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("暂无历史记录")
    
    def run(self):
        """运行主应用"""
        # 首先初始化选股器
        if not self.initialize_selector():
            st.error("系统初始化失败，无法继续")
            return
            
        self.render_header()
        
        # 侧边栏配置
        config = self.render_sidebar()
            
        # 显示选股器状态
        if hasattr(st.session_state, 'is_real_selector'):
            if st.session_state.is_real_selector:
                st.sidebar.success("🎯 真实数据模式")
                st.sidebar.info("使用真实股票数据和选股算法")
            else:
                st.sidebar.warning("🎭 演示模式")
                st.sidebar.info("使用模拟数据进行功能演示")
        
        # 主内容区域
        main_tabs = st.tabs(["🏠 主页", "🔍 开始扫描", "📊 扫描结果", "📥 导出&历史"])
        
        with main_tabs[0]:
            st.markdown("""
            ## 欢迎使用A股选股系统
            
            ### 🎯 系统功能
            - **智能选股**: 基于技术分析的多维度选股策略
            - **实时扫描**: 支持全市场股票实时扫描
            - **规则引擎**: 黄金坑、趋势突破等成熟选股规则
            - **结果分析**: 详细的选股结果和规则表现分析
            - **数据导出**: 支持CSV、JSON等多种格式导出
            
            ### 📈 支持的选股策略
            1. **黄金坑规则**: 检测深度回撤后的反转突破机会
            2. **趋势突破规则**: 识别多头趋势和放量突破信号
            
            ### 🚀 快速开始
            1. 在左侧配置面板设置扫描参数
            2. 选择需要的选股规则
            3. 点击"开始扫描"标签页执行扫描
            4. 在"扫描结果"中查看详细结果
            """)
        
        with main_tabs[1]:
            st.subheader("🔍 股票扫描")
            
            # 扫描准备状态或完成状态  
            if hasattr(st.session_state, 'scan_results') and st.session_state.scan_results:
                # 扫描已完成，显示结果和重新扫描按钮
                results_count = len(st.session_state.scan_results.get('results', []))
                st.success(f"✅ {st.session_state.last_scan_config.get('scan_mode', '扫描')}完成！找到 {results_count} 只符合条件的股票")
                
                # 重新扫描按钮
                if st.button("🔄 重新扫描", type="secondary", use_container_width=True, key="restart_scan"):
                    # 清除之前的结果并设置新扫描状态
                    st.session_state.scan_running = True
                    st.session_state.scan_started = False
                    st.session_state.scan_results = None
                    
                    # 立即显示重新扫描的反馈
                    st.success("🔄 开始重新扫描...")
                    
                    # 创建进度显示区域
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    status_text.text("正在初始化扫描...")
                    
                    # 立即执行扫描，不等待下次渲染
                    self.run_stock_scan_inline(st.session_state.last_scan_config, progress_bar, status_text)
            else:
                # 准备开始扫描
                if hasattr(st.session_state, 'is_real_selector') and st.session_state.is_real_selector:
                    st.info("🎯 真实数据模式 - 将获取实际股票数据进行分析")
                    if config['scan_mode'] in ["深市主板", "全部板块"]:
                        st.warning("⏰ 深市主板或全部板块扫描需要较长时间，请耐心等待")
                else:
                    st.info("🎭 演示模式 - 使用模拟数据快速演示")
                
                # 开始扫描按钮
                if st.button("🚀 开始选股扫描", type="primary", use_container_width=True, key="start_scan_btn"):
                    # 设置扫描状态和配置
                    st.session_state.scan_running = True
                    st.session_state.last_scan_config = config
                    st.session_state.scan_progress = {'current': 0, 'total': 1, 'found': 0}
                    st.session_state.scan_started = False
                    
                    # 立即显示扫描开始的反馈
                    st.success("🚀 开始扫描...")
                    
                    # 创建进度显示区域
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    status_text.text("正在初始化扫描...")
                    
                    # 立即执行扫描，不等待下次渲染
                    self.run_stock_scan_inline(config, progress_bar, status_text)
        
        with main_tabs[2]:
            self.render_results()
        
        with main_tabs[3]:
            self.render_export_section()


class MockStockSelector:
    """模拟选股器类，用于演示界面功能"""
    
    def scan_stocks_advanced(self, symbols, rule_names=None, min_score=60.0, 
                           max_workers=5, save_results=False, progress_callback=None, max_results=50):
        """模拟高级扫描功能"""
        import random
        import time
        
        results = []
        total = len(symbols)
        
        # 模拟扫描过程
        for i, symbol in enumerate(symbols):
            # 模拟处理时间
            time.sleep(0.1)
            
            # 随机生成结果
            if random.random() < 0.3:  # 30%的概率符合条件
                composite_score = random.uniform(min_score, 95.0)
                
                rule_results = []
                rule_specific_data = {}
                
                for rule_name in (rule_names or ['GoldenPit', 'TrendBreakout']):
                    result_type = random.choice(['PASS', 'FAIL', 'PARTIAL'])
                    score = random.uniform(50.0, 95.0) if result_type == 'PASS' else random.uniform(0.0, 60.0)
                    confidence = random.uniform(70.0, 95.0)
                    
                    rule_results.append(MockRuleResult(rule_name, result_type, score, confidence))
                    
                    # 为每个规则添加特定数据
                    if rule_name == 'GoldenPit':
                        rule_specific_data['GoldenPit'] = {
                            'current_price': round(random.uniform(8.50, 45.80), 2),
                            'trigger_date': '2024-08-25',
                            'previous_high': round(random.uniform(50.0, 80.0), 2),
                            'max_drawdown': f"-{random.uniform(20.0, 35.0):.1f}%",
                            'big_yang_gain': f"{random.uniform(5.0, 12.0):.1f}%",
                            'ma10': round(random.uniform(8.0, 44.0), 2)
                        }
                    elif rule_name == 'TrendBreakout':
                        prev_high = round(random.uniform(30.0, 60.0), 2)
                        current = round(prev_high * random.uniform(1.008, 1.025), 2)
                        rule_specific_data['TrendBreakout'] = {
                            'current_price': current,
                            'trigger_date': '2024-08-25', 
                            'previous_high': prev_high,
                            'breakout_margin': f"+{((current - prev_high) / prev_high * 100):.1f}%",
                            'volume_days': f"{random.randint(2, 5)}天",
                            'avg_volume_ratio': round(random.uniform(1.3, 2.8), 2)
                        }
                
                stock_result = {
                    'symbol': symbol,
                    'stock_name': f'模拟股票{symbol[-3:]}',
                    'composite_score': composite_score,
                    'results': rule_results,
                    'rule_data': rule_specific_data,
                    'data_info': {
                        'data_length': random.randint(100, 250),
                        'date_range': '2024-01-01 to 2024-08-26',
                        'indicators_count': 24
                    },
                    'score_details': {rule.rule_name: rule.score for rule in rule_results}
                }
                
                results.append(stock_result)
            
            # 调用进度回调
            if progress_callback:
                progress_callback(i + 1, total, len(results))
        
        # 按评分排序
        results.sort(key=lambda x: x['composite_score'], reverse=True)
        
        # 限制返回结果数量
        qualified_results = results[:max_results] if len(results) > max_results else results
        
        return {
            'results': qualified_results,
            'statistics': {
                'total_symbols': total,
                'qualified_stocks': len(results),
                'returned_stocks': len(qualified_results),
                'qualification_rate': len(results) / total * 100 if total > 0 else 0,
                'total_processing_time': total * 0.1
            }
        }


class MockRuleResult:
    """模拟规则结果类"""
    
    def __init__(self, rule_name, result_name, score, confidence):
        self.rule_name = rule_name
        self.result = MockResult(result_name)
        self.score = score
        self.confidence = confidence


class MockResult:
    """模拟结果枚举类"""
    
    def __init__(self, name):
        self.name = name


# 主程序入口
if __name__ == "__main__":
    app = StockSelectionApp()
    app.run()