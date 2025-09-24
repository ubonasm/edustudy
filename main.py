import streamlit as st
import requests
import re
from datetime import datetime
import time
import csv
import io

def search_papers_api(query, limit=20):
    """Semantic Scholar APIを使用して論文を検索する関数"""
    if not query:
        return []
    
    time.sleep(1)  # APIリクエスト間に1秒待機
    
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
    
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            headers = {
                'User-Agent': 'Academic Paper Search Tool (educational use)',
                'Accept': 'application/json'
            }
            
            response = requests.get(base_url, params=params, headers=headers, timeout=15)
            
            if response.status_code == 429:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)  # 指数バックオフ
                    st.warning(f"API制限に達しました。{wait_time}秒後にリトライします... (試行 {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    st.error("API制限により検索できませんでした。しばらく時間をおいてから再度お試しください。")
                    return []
            
            response.raise_for_status()
            data = response.json()
            
            papers = []
            for paper in data.get('data', []):
                # 教育関係の論文をフィルタリング
                title = paper.get('title') or ''
                abstract = paper.get('abstract') or ''
                title_abstract = (title + ' ' + abstract).lower()
                education_terms = ['education', 'learning', 'teaching', 'student', 'school', 'classroom', 'pedagogy', 'curriculum', 'instruction']
                
                if any(term in title_abstract for term in education_terms):
                    authors_list = paper.get('authors', [])
                    if authors_list:
                        authors_names = []
                        for author in authors_list:
                            if author and isinstance(author, dict):
                                name = author.get('name')
                                if name:
                                    authors_names.append(str(name))
                        authors_str = ', '.join(authors_names) if authors_names else '著者不明'
                    else:
                        authors_str = '著者不明'
                    
                    processed_paper = {
                        'title': str(title) if title else 'タイトル不明',
                        'authors': authors_str,
                        'year': paper.get('year') if paper.get('year') is not None else '年度不明',
                        'abstract': str(abstract) if abstract else '抄録なし',
                        'venue': str(paper.get('venue')) if paper.get('venue') else '掲載誌不明',
                        'citation_count': paper.get('citationCount', 0) or 0,
                        'url': str(paper.get('url')) if paper.get('url') else '',
                        'publication_date': str(paper.get('publicationDate')) if paper.get('publicationDate') else ''
                    }
                    papers.append(processed_paper)
            
            return papers
        
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                st.warning(f"接続エラーが発生しました。{retry_delay}秒後にリトライします... (試行 {attempt + 1}/{max_retries})")
                time.sleep(retry_delay)
                continue
            else:
                st.error(f"API接続エラー: {str(e)}")
                st.info("💡 解決方法: しばらく時間をおいてから再度検索してください。または検索語を変更してみてください。")
                return []
        except Exception as e:
            st.error(f"検索エラー: {str(e)}")
            return []
    
    return []

def highlight_text(text, search_terms):
    """検索語をハイライトする関数"""
    if not search_terms or not text or text == 'None':
        return str(text) if text else ''
    
    # 文字列に変換して安全に処理
    text = str(text)
    search_terms = str(search_terms)
    
    # 複数の検索語に対応
    terms = [term.strip() for term in search_terms.split() if term.strip()]
    highlighted_text = text
    
    for term in terms:
        if term:  # 空文字列チェック
            # 大文字小文字を区別しない検索
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            highlighted_text = pattern.sub(
                f'<mark style="background-color: #ffeb3b; padding: 2px 4px; border-radius: 3px; font-weight: bold;">{term}</mark>',
                highlighted_text
            )
    
    return highlighted_text

def format_apa_citation(paper):
    """APA ver.7形式で引用文献を作成する関数"""
    authors = paper.get('authors', '著者不明')
    year = paper.get('year', '年度不明')
    title = paper.get('title', 'タイトル不明')
    venue = paper.get('venue', '掲載誌不明')
    url = paper.get('url', '')
    
    # 著者名の処理（APA形式: Last, F. M.）
    if authors != '著者不明':
        # 簡略化：実際のAPA形式では姓名の順序変更が必要
        author_formatted = authors
    else:
        author_formatted = '著者不明'
    
    # 年度の処理
    year_formatted = f"({year})" if year != '年度不明' else "(年度不明)"
    
    # タイトルの処理（APA形式では文の最初の単語のみ大文字）
    title_formatted = title
    
    # 掲載誌の処理（イタリック体を示すため*で囲む）
    venue_formatted = f"*{venue}*" if venue != '掲載誌不明' else "*掲載誌不明*"
    
    # URL処理
    url_formatted = f" {url}" if url else ""
    
    # APA形式の引用文献作成
    citation = f"{author_formatted} {year_formatted}. {title_formatted}. {venue_formatted}.{url_formatted}"
    
    return citation

def format_bibtex_citation(paper, index):
    """BibTeX形式で引用文献を作成する関数"""
    # 必要な情報を取得
    title = paper.get('title', 'Unknown Title')
    authors = paper.get('authors', 'Unknown Author')
    year = paper.get('year', 'Unknown')
    venue = paper.get('venue', 'Unknown Venue')
    url = paper.get('url', '')
    
    # BibTeX用のキーを生成（著者の姓+年度+タイトルの最初の単語）
    first_author = authors.split(',')[0].split()[-1] if authors != 'Unknown Author' else 'Unknown'
    first_word = title.split()[0] if title != 'Unknown Title' else 'Unknown'
    bibtex_key = f"{first_author}{year}{first_word}".replace(' ', '').replace(',', '')
    
    # 著者名をBibTeX形式に変換（Last, First and Last, First）
    if authors != 'Unknown Author':
        author_list = [author.strip() for author in authors.split(',')]
        bibtex_authors = ' and '.join(author_list)
    else:
        bibtex_authors = 'Unknown Author'
    
    # 論文の種類を判定（簡易版）
    venue_lower = venue.lower() if venue != 'Unknown Venue' else ''
    if any(word in venue_lower for word in ['conference', 'proceedings', 'workshop', 'symposium']):
        entry_type = 'inproceedings'
        venue_field = 'booktitle'
    elif any(word in venue_lower for word in ['journal', 'transactions', 'letters']):
        entry_type = 'article'
        venue_field = 'journal'
    else:
        entry_type = 'misc'
        venue_field = 'howpublished'
    
    # BibTeX形式の文献情報を作成
    bibtex_entry = f"""@{entry_type}{{{bibtex_key},
  title = {{{title}}},
  author = {{{bibtex_authors}}},
  {venue_field} = {{{venue}}},
  year = {{{year}}}"""
    
    # URLがある場合は追加
    if url:
        bibtex_entry += f",\n  url = {{{url}}}"
    
    # 抄録がある場合は追加
    abstract = paper.get('abstract', '')
    if abstract and abstract != '抄録なし' and len(abstract) > 10:
        # 抄録を適切にエスケープ
        clean_abstract = abstract.replace('{', '\\{').replace('}', '\\}').replace('%', '\\%')
        bibtex_entry += f",\n  abstract = {{{clean_abstract}}}"
    
    bibtex_entry += "\n}"
    
    return bibtex_entry

def create_csv_data(papers, search_query):
    """検索結果をCSV形式のデータに変換する関数"""
    csv_data = []
    
    # ヘッダー行
    headers = [
        'No.', 'title', 'author', 'year', 'journal', 'cites', 
        'abstract', 'URL', 'APA style', 'search words', 'search date'
    ]
    csv_data.append(headers)
    
    # データ行
    search_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    for i, paper in enumerate(papers, 1):
        row = [
            i,
            paper.get('title', 'タイトル不明'),
            paper.get('authors', '著者不明'),
            paper.get('year', '年度不明'),
            paper.get('venue', '掲載誌不明'),
            paper.get('citation_count', 0),
            paper.get('abstract', '抄録なし'),
            paper.get('url', ''),
            format_apa_citation(paper),
            search_query,
            search_datetime
        ]
        csv_data.append(row)
    
    return csv_data

def create_csv_download(papers, search_query):
    """CSVダウンロード用のデータを作成する関数"""
    csv_data = create_csv_data(papers, search_query)
    
    # StringIOを使用してCSVデータを作成
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerows(csv_data)
    
    return output.getvalue()

def create_bibtex_data(papers):
    """保存された論文をBibTeX形式のデータに変換する関数"""
    bibtex_entries = []
    
    for i, paper in enumerate(papers, 1):
        bibtex_entry = format_bibtex_citation(paper, i)
        bibtex_entries.append(bibtex_entry)
    
    # BibTeX形式のファイルヘッダーを追加
    header = f"""% BibTeX bibliography file
% Generated by Academic Paper Search Tool
% Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
% Total entries: {len(papers)}

"""
    
    return header + '\n\n'.join(bibtex_entries)

def display_paper_with_save(paper, search_query, index):
    """論文情報を保存ボタン付きで表示する関数"""
    with st.container():
        title = str(paper.get('title', 'タイトル不明'))
        highlighted_title = highlight_text(title, search_query)
        
        # タイトルと保存ボタンを同じ行に配置
        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown(f"### {index}. {highlighted_title}", unsafe_allow_html=True)
        with col2:
            # 個別保存ボタン
            save_key = f"save_{index}_{hash(title)}"
            if st.button("💾", key=save_key, help="この論文を保存"):
                # 重複チェック
                existing_titles = [p.get('title') for p in st.session_state.saved_papers]
                if title not in existing_titles:
                    st.session_state.saved_papers.append(paper)
                    st.success("論文を保存しました！")
                    st.rerun()
                else:
                    st.warning("この論文は既に保存されています")
        
        # 著者情報と年度
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            authors = str(paper.get('authors', '著者不明'))
            st.markdown(f"**著者:** {authors}")
        with col2:
            year = paper.get('year', '年度不明')
            st.markdown(f"**年度:** {year}")
        with col3:
            citation_count = paper.get('citation_count', 0)
            st.markdown(f"**引用数:** {citation_count}")
        
        # 掲載誌情報
        venue = paper.get('venue')
        if venue and venue != '掲載誌不明':
            st.markdown(f"**掲載誌:** {str(venue)}")
        
        # APA引用形式を表示
        apa_citation = format_apa_citation(paper)
        bibtex_citation = format_bibtex_citation(paper, index)
        
        col1, col2 = st.columns(2)
        with col1:
            with st.expander("📝 APA引用形式"):
                st.code(apa_citation, language="text")
        with col2:
            with st.expander("📚 BibTeX引用形式"):
                st.code(bibtex_citation, language="bibtex")
        
        # 抄録（ハイライト付き）
        abstract = paper.get('abstract')
        if abstract and abstract != '抄録なし' and abstract != 'None':
            abstract_str = str(abstract)
            # 抄録を適切な長さに制限
            if len(abstract_str) > 300:
                truncated_abstract = abstract_str[:300] + "..."
                highlighted_abstract = highlight_text(truncated_abstract, search_query)
            else:
                highlighted_abstract = highlight_text(abstract_str, search_query)
            st.markdown(f"**抄録:** {highlighted_abstract}", unsafe_allow_html=True)
        
        # 論文リンク
        url = paper.get('url')
        if url and url != '':
            st.markdown(f"[📄 論文を読む]({url})")
        
        st.markdown("---")

def main():
    # ページ設定
    st.set_page_config(
        page_title="EduStudy",
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
    
    # セッション状態の初期化
    if 'saved_papers' not in st.session_state:
        st.session_state.saved_papers = []
    if 'last_search_query' not in st.session_state:
        st.session_state.last_search_query = ""
    
    # ヘッダー
    st.markdown("""
    <div class="main-header">
        <h1>📚 EduStudy</h1>
        <p>世界中の教育関係論文をリアルタイムで検索できます。</p>
    </div>
    """, unsafe_allow_html=True)
    
    # サイドバー
    with st.sidebar:
        st.header("🔍 検索オプション")
        
        # 検索結果数の設定
        result_limit = st.slider(
            "検索結果数",
            min_value=5,
            max_value=100,
            value=20,
            step=5
        )
        
        # 年度フィルター
        current_year = datetime.now().year
        year_range = st.slider(
            "発行年度範囲",
            min_value=1950,
            max_value=current_year,
            value=(2025, current_year),
            step=1
        )
        
        st.markdown("---")
        
        st.header("💾 保存された論文")
        
        if st.session_state.saved_papers:
            st.success(f"保存済み: {len(st.session_state.saved_papers)}件")
            
            # CSVダウンロードボタン
            if st.button("📥 Download for CSV file", use_container_width=True):
                csv_content = create_csv_download(
                    st.session_state.saved_papers, 
                    st.session_state.last_search_query
                )
                
                filename = f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                
                st.download_button(
                    label="📄 Download for CSV file",
                    data=csv_content,
                    file_name=filename,
                    mime="text/csv",
                    use_container_width=True
                )
            
            # BibTeXダウンロードボタン
            if st.button("📚 Download for BibTeX file", use_container_width=True):
                bibtex_content = create_bibtex_data(st.session_state.saved_papers)
                
                filename = f"論文検索結果_{datetime.now().strftime('%Y%m%d_%H%M%S')}.bib"
                
                st.download_button(
                    label="📖 Download for BibTeX file",
                    data=bibtex_content,
                    file_name=filename,
                    mime="text/plain",
                    use_container_width=True
                )
            
            # 保存リストをクリア
            if st.button("🗑️ 保存リストをクリア", use_container_width=True):
                st.session_state.saved_papers = []
                st.success("保存リストをクリアしました")
                st.rerun()
            
            # 保存された論文の一覧表示
            with st.expander("📋 保存された論文一覧"):
                for i, paper in enumerate(st.session_state.saved_papers, 1):
                    st.write(f"{i}. {paper.get('title', 'タイトル不明')}")
                    st.write(f"   著者: {paper.get('authors', '著者不明')}")
                    st.write(f"   年度: {paper.get('year', '年度不明')}")
                    st.write("---")
        else:
            st.info("保存された論文はありません")
        
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
        # 検索クエリを保存
        st.session_state.last_search_query = search_query
        
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
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("💾 全ての結果を保存", type="secondary"):
                    # 重複を避けて保存
                    new_papers = []
                    existing_titles = [p.get('title') for p in st.session_state.saved_papers]
                    
                    for paper in results:
                        if paper.get('title') not in existing_titles:
                            new_papers.append(paper)
                    
                    st.session_state.saved_papers.extend(new_papers)
                    st.success(f"{len(new_papers)}件の新しい論文を保存しました")
                    st.rerun()
            
            with col2:
                if st.session_state.saved_papers:
                    download_format = st.selectbox(
                        "The Download Format",
                        ["CSV", "BibTeX"],
                        key="download_format_main"
                    )
                    
                    if download_format == "CSV":
                        csv_content = create_csv_download(
                            st.session_state.saved_papers, 
                            search_query
                        )
                        filename = f"論文検索結果_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                        mime_type = "text/csv"
                        file_content = csv_content
                        button_label = "📥 CSVダウンロード"
                    else:  # BibTeX
                        bibtex_content = create_bibtex_data(st.session_state.saved_papers)
                        filename = f"論文検索結果_{datetime.now().strftime('%Y%m%d_%H%M%S')}.bib"
                        mime_type = "text/plain"
                        file_content = bibtex_content
                        button_label = "📚 BibTeXダウンロード"
                    
                    st.download_button(
                        label=button_label,
                        data=file_content,
                        file_name=filename,
                        mime=mime_type,
                        type="primary"
                    )
            
            # 各論文の表示
            for i, paper in enumerate(results, 1):
                display_paper_with_save(paper, search_query, i)
                
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
        <p>📚 EduStudy: 教育関係学会誌論文検索システム</p>
        <p>Powered by Semantic Scholar API | データは定期的に更新されます</p>
        <p>研究者の学術活動を支援します</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
