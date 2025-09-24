import streamlit as st
import requests
import re
from datetime import datetime
import time

def search_papers_api(query, limit=20):
    """Semantic Scholar APIを使用して論文を検索する関数"""
    if not query:
        return []
    
    # Semantic Scholar API endpoint
    base_url = "https://api.semanticscholar.org/graph/v1/paper/search"
    
    # 教育関係のキーワードを追加して検索精度を向上
    education_keywords = ["education", "learning", "teaching", "pedagogy", "educational"]
    enhanced_query = f"{query} {' OR '.join(education_keywords)}"
    
    params = {
        'query': enhanced_query,
        'limit': limit,
        'fields': 'paperId,title,authors,year,abstract,venue,citationCount,publicationDate,url'
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        papers = []
        for paper in data.get('data', []):
            # 教育関係の論文をフィルタリング
            title_abstract = (paper.get('title', '') + ' ' + paper.get('abstract', '')).lower()
            education_terms = ['education', 'learning', 'teaching', 'student', 'school', 'classroom', 'pedagogy', 'curriculum', 'instruction']
            
            if any(term in title_abstract for term in education_terms):
                processed_paper = {
                    'title': paper.get('title', 'タイトル不明'),
                    'authors': ', '.join([author.get('name', '') for author in paper.get('authors', [])]) or '著者不明',
                    'year': paper.get('year', '年度不明'),
                    'abstract': paper.get('abstract', '抄録なし'),
                    'venue': paper.get('venue', '掲載誌不明'),
                    'citation_count': paper.get('citationCount', 0),
                    'url': paper.get('url', ''),
                    'publication_date': paper.get('publicationDate', '')
                }
                papers.append(processed_paper)
        
        return papers
    
    except requests.exceptions.RequestException as e:
        st.error(f"API接続エラー: {str(e)}")
        return []
    except Exception as e:
        st.error(f"検索エラー: {str(e)}")
        return []

def highlight_text(text, search_terms):
    """検索語をハイライトする関数"""
    if not search_terms or not text:
        return text
    
    # 複数の検索語に対応
    terms = [term.strip() for term in search_terms.split() if term.strip()]
    highlighted_text = text
    
    for term in terms:
        # 大文字小文字を区別しない検索
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        highlighted_text = pattern.sub(
            f'<mark style="background-color: #ffeb3b; padding: 2px 4px; border-radius: 3px; font-weight: bold;">{term}</mark>',
            highlighted_text
        )
    
    return highlighted_text

def display_paper(paper, search_query, index):
    """論文情報を表示する関数"""
    with st.container():
        # 論文番号とタイトル（ハイライト付き）
        highlighted_title = highlight_text(paper['title'], search_query)
        st.markdown(f"### {index}. {highlighted_title}", unsafe_allow_html=True)
        
        # 著者情報と年度
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.markdown(f"**著者:** {paper['authors']}")
        with col2:
            st.markdown(f"**年度:** {paper['year']}")
        with col3:
            st.markdown(f"**引用数:** {paper['citation_count']}")
        
        # 掲載誌情報
        if paper['venue']:
            st.markdown(f"**掲載誌:** {paper['venue']}")
        
        # 抄録（ハイライト付き）
        if paper['abstract'] and paper['abstract'] != '抄録なし':
            highlighted_abstract = highlight_text(paper['abstract'], search_query)
            # 抄録を適切な長さに制限
            if len(paper['abstract']) > 300:
                truncated_abstract = paper['abstract'][:300] + "..."
                highlighted_abstract = highlight_text(truncated_abstract, search_query)
            st.markdown(f"**抄録:** {highlighted_abstract}", unsafe_allow_html=True)
        
        # 論文リンク
        if paper['url']:
            st.markdown(f"[📄 論文を読む]({paper['url']})")
        
        st.markdown("---")

def main():
    # ページ設定
    st.set_page_config(
        page_title="教育関係学会誌論文検索システム",
        page_icon="📚",
        layout="wide"
    )
    
    # カスタムCSS
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
    }
    .search-box {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .paper-card {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # ヘッダー
    st.markdown("""
    <div class="main-header">
        <h1>📚 教育関係学会誌論文検索システム</h1>
        <p>世界中の教育関係論文をリアルタイムで検索できます。Semantic Scholar APIを使用して最新の研究成果を提供します。</p>
    </div>
    """, unsafe_allow_html=True)
    
    # サイドバー
    with st.sidebar:
        st.header("🔍 検索オプション")
        
        # 検索結果数の設定
        result_limit = st.slider(
            "検索結果数",
            min_value=5,
            max_value=50,
            value=20,
            step=5
        )
        
        # 年度フィルター
        current_year = datetime.now().year
        year_range = st.slider(
            "発行年度範囲",
            min_value=2000,
            max_value=current_year,
            value=(2020, current_year),
            step=1
        )
        
        st.markdown("---")
        st.markdown("**💡 検索のヒント:**")
        st.markdown("- 日本語または英語で検索可能")
        st.markdown("- 複数のキーワードをスペースで区切って入力")
        st.markdown("- 教育関係の論文に特化して検索")
        st.markdown("- 引用数の多い論文が上位に表示")
        
        st.markdown("---")
        st.markdown("**📊 データソース:**")
        st.markdown("- Semantic Scholar API")
        st.markdown("- 200M+ 学術論文データベース")
        st.markdown("- リアルタイム更新")
    
    # メイン検索エリア
    st.markdown('<div class="search-box">', unsafe_allow_html=True)
    
    col1, col2 = st.columns([4, 1])
    
    with col1:
        search_query = st.text_input(
            "🔍 検索語を入力してください",
            placeholder="例: デジタル教材, collaborative learning, AI education",
            help="日本語または英語で検索できます。複数のキーワードをスペースで区切って入力してください。"
        )
    
    with col2:
        search_button = st.button("🚀 検索開始", type="primary", use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 検索実行
    if search_query and (search_button or search_query):
        with st.spinner("🔍 論文を検索中..."):
            # プログレスバー表示
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("Semantic Scholar APIに接続中...")
            progress_bar.progress(25)
            
            # API検索実行
            results = search_papers_api(search_query, result_limit)
            progress_bar.progress(75)
            
            # 年度フィルタリング
            if results:
                filtered_results = [
                    paper for paper in results 
                    if paper['year'] != '年度不明' and 
                    isinstance(paper['year'], int) and 
                    year_range[0] <= paper['year'] <= year_range[1]
                ]
                results = filtered_results
            
            progress_bar.progress(100)
            status_text.text("検索完了!")
            time.sleep(0.5)
            progress_bar.empty()
            status_text.empty()
        
        # 結果表示
        st.markdown(f"## 📊 検索結果: {len(results)}件")
        
        if results:
            # 結果の統計情報
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📄 検索結果数", len(results))
            with col2:
                result_years = [paper['year'] for paper in results if isinstance(paper['year'], int)]
                st.metric("📅 最新年度", max(result_years) if result_years else "N/A")
            with col3:
                total_citations = sum([paper['citation_count'] for paper in results])
                st.metric("📈 総引用数", total_citations)
            with col4:
                unique_venues = len(set([paper['venue'] for paper in results if paper['venue']]))
                st.metric("📚 関連学会誌数", unique_venues)
            
            st.markdown("---")
            
            # 引用数でソート
            sorted_results = sorted(results, key=lambda x: x['citation_count'], reverse=True)
            
            # 各論文の表示
            for i, paper in enumerate(sorted_results, 1):
                display_paper(paper, search_query, i)
                
        else:
            st.warning("🔍 検索条件に一致する論文が見つかりませんでした。")
            st.markdown("""
            **💡 検索のコツ:**
            - より一般的なキーワードを使用してみてください
            - 英語のキーワードも試してみてください
            - キーワードの数を減らしてみてください
            - 年度範囲を広げてみてください
            """)
    
    else:
        # 初期表示：システム説明
        st.markdown("## 🎯 システムについて")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### 🔍 検索機能
            - **リアルタイム検索**: Semantic Scholar APIを使用
            - **多言語対応**: 日本語・英語での検索が可能
            - **教育特化**: 教育関係の論文に特化したフィルタリング
            - **ハイライト表示**: 検索語を結果内でハイライト
            """)
            
        with col2:
            st.markdown("""
            ### 📊 データベース
            - **200M+ 論文**: 世界最大級の学術論文データベース
            - **リアルタイム更新**: 最新の研究成果を即座に検索
            - **引用情報**: 論文の影響度を引用数で確認
            - **直接リンク**: 論文の原文へ直接アクセス可能
            """)
        
        st.markdown("---")
        
        st.markdown("""
        ### 🚀 使い方
        1. **検索語入力**: 上の検索ボックスに関心のあるキーワードを入力
        2. **オプション設定**: サイドバーで検索結果数や年度範囲を調整
        3. **検索実行**: 「検索開始」ボタンをクリック
        4. **結果確認**: ハイライト表示された検索結果を確認
        5. **論文閲覧**: 気になる論文のリンクをクリックして原文を読む
        """)
    
    # フッター
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: gray; font-size: 0.8em; padding: 2rem;'>
        <p>📚 教育関係学会誌論文検索システム</p>
        <p>Powered by Semantic Scholar API | データは定期的に更新されます</p>
        <p>🔬 研究者の皆様の学術活動を支援します</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
