"""
アプリケーション設計のためのファイルテンプレート
"""

from typing import Dict, List, Optional, Union

# アプリ設計書テンプレート
APP_DESIGN_TEMPLATE = """# {app_name} - アプリケーション設計書

## 1. アプリケーション概要
**名称**: {app_name}
**バージョン**: {version}
**概要**: {app_description}

## 2. ビジネス要件
{business_requirements}

## 3. 機能要件
{functional_requirements}

## 4. 技術仕様
### 4.1 アーキテクチャ
{architecture}

### 4.2 使用技術・フレームワーク
{technology_stack}

### 4.3 データモデル
{data_model}

## 5. ユーザーインターフェイス
{ui_description}

## 6. API設計
{api_design}

## 7. セキュリティ要件
{security_requirements}

## 8. パフォーマンス要件
{performance_requirements}

## 9. スケジュールと工数
{schedule}

## 10. 付録
{appendix}
"""

# アプリプロトタイプHTML/CSSテンプレート
APP_PROTOTYPE_TEMPLATE = """<!DOCTYPE html>
<html lang="{language}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{app_name}</title>
    <style>
        /* リセットCSS */
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f7;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        header {{
            background-color: #fff;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 15px 0;
            position: sticky;
            top: 0;
            z-index: 100;
        }}
        
        .header-content {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0 20px;
        }}
        
        .logo {{
            font-size: 24px;
            font-weight: bold;
            color: #333;
        }}
        
        .nav-menu {{
            display: flex;
            list-style: none;
        }}
        
        .nav-menu li {{
            margin-left: 20px;
        }}
        
        .nav-menu a {{
            text-decoration: none;
            color: #555;
            font-weight: 500;
            transition: color 0.3s;
        }}
        
        .nav-menu a:hover {{
            color: #007aff;
        }}
        
        .hero {{
            background-color: #007aff;
            color: white;
            padding: 60px 20px;
            text-align: center;
            margin-bottom: 40px;
        }}
        
        .hero h1 {{
            font-size: 48px;
            margin-bottom: 20px;
        }}
        
        .hero p {{
            font-size: 20px;
            max-width: 800px;
            margin: 0 auto 30px;
        }}
        
        .btn {{
            display: inline-block;
            background-color: #fff;
            color: #007aff;
            padding: 12px 30px;
            border-radius: 30px;
            text-decoration: none;
            font-weight: bold;
            transition: all 0.3s;
        }}
        
        .btn:hover {{
            background-color: rgba(255,255,255,0.9);
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
        
        .features {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
            margin-bottom: 60px;
        }}
        
        .feature-card {{
            background-color: #fff;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.05);
            transition: transform 0.3s;
        }}
        
        .feature-card:hover {{
            transform: translateY(-5px);
        }}
        
        .feature-card h3 {{
            font-size: 24px;
            margin-bottom: 15px;
            color: #007aff;
        }}
        
        .feature-card p {{
            color: #666;
        }}
        
        footer {{
            background-color: #333;
            color: #fff;
            padding: 40px 0;
            text-align: center;
        }}
        
        .footer-content {{
            max-width: 800px;
            margin: 0 auto;
        }}
        
        /* レスポンシブデザイン */
        @media (max-width: 768px) {{
            .header-content {{
                flex-direction: column;
                text-align: center;
            }}
            
            .nav-menu {{
                margin-top: 15px;
            }}
            
            .hero h1 {{
                font-size: 36px;
            }}
            
            .hero p {{
                font-size: 18px;
            }}
        }}
        
        /* カスタムスタイル */
        {custom_css}
    </style>
</head>
<body>
    <header>
        <div class="header-content">
            <div class="logo">{app_name}</div>
            <ul class="nav-menu">
                {nav_items}
            </ul>
        </div>
    </header>
    
    <section class="hero">
        <h1>{app_headline}</h1>
        <p>{app_subheadline}</p>
        <a href="#" class="btn">{cta_text}</a>
    </section>
    
    <div class="container">
        <div class="features">
            {feature_cards}
        </div>
    </div>
    
    <footer>
        <div class="footer-content">
            <p>&copy; {current_year} {app_name}. All rights reserved.</p>
        </div>
    </footer>
</body>
</html>
"""

# モックアップ用のレスポンシブナビゲーションアイテム生成
def generate_nav_items(items: List[str]) -> str:
    return "\n                ".join([f'<li><a href="#">{item}</a></li>' for item in items])

# 機能カード生成
def generate_feature_cards(features: List[Dict[str, str]]) -> str:
    cards = []
    for feature in features:
        card = f"""
            <div class="feature-card">
                <h3>{feature['title']}</h3>
                <p>{feature['description']}</p>
            </div>"""
        cards.append(card)
    return "\n".join(cards)

# アプリ仕様書の生成
def generate_app_spec(
    app_name: str,
    app_description: str,
    features: List[Dict[str, str]],
    architecture: str,
    technologies: List[str],
    data_model: Optional[str] = None,
    api_endpoints: Optional[List[Dict[str, str]]] = None,
    language: str = "ja"
) -> str:
    """
    アプリ仕様書を生成する
    
    Args:
        app_name: アプリケーション名
        app_description: アプリケーションの説明
        features: 機能リスト（辞書のリスト、各辞書はtitleとdescriptionを含む）
        architecture: アーキテクチャの説明
        technologies: 使用技術リスト
        data_model: データモデルの説明（省略可）
        api_endpoints: APIエンドポイントのリスト（省略可）
        language: 言語コード（デフォルトは日本語）
        
    Returns:
        生成されたアプリ仕様書
    """
    # 機能要件の組み立て
    functional_requirements = "\n".join([f"- **{f['title']}**: {f['description']}" for f in features])
    
    # 使用技術の組み立て
    tech_stack = "\n".join([f"- {tech}" for tech in technologies])
    
    # APIエンドポイントの組み立て
    api_design = ""
    if api_endpoints:
        for endpoint in api_endpoints:
            api_design += f"- **{endpoint.get('method', 'GET')} {endpoint.get('path', '/')}**: {endpoint.get('description', '')}\n"
    
    # テンプレート変数の準備
    template_vars = {
        "app_name": app_name,
        "version": "1.0.0",
        "app_description": app_description,
        "business_requirements": "（ここにビジネス要件を記述）",
        "functional_requirements": functional_requirements,
        "architecture": architecture,
        "technology_stack": tech_stack,
        "data_model": data_model or "（ここにデータモデルを記述）",
        "ui_description": "（ここにUIの説明を記述）",
        "api_design": api_design or "（ここにAPI設計を記述）",
        "security_requirements": "（ここにセキュリティ要件を記述）",
        "performance_requirements": "（ここにパフォーマンス要件を記述）",
        "schedule": "（ここにスケジュールと工数を記述）",
        "appendix": "（ここに付録情報を記述）"
    }
    
    return APP_DESIGN_TEMPLATE.format(**template_vars)

# アプリプロトタイプHTML生成
def generate_app_prototype(
    app_name: str,
    app_headline: str,
    app_subheadline: str,
    features: List[Dict[str, str]],
    nav_items: List[str] = None,
    cta_text: str = "始める",
    custom_css: str = "",
    language: str = "ja",
    current_year: str = "2025"
) -> str:
    """
    アプリプロトタイプHTMLを生成する
    
    Args:
        app_name: アプリケーション名
        app_headline: メインの見出し
        app_subheadline: サブ見出し
        features: 機能リスト（辞書のリスト、各辞書はtitleとdescriptionを含む）
        nav_items: ナビゲーションアイテムのリスト（省略可）
        cta_text: CTAボタンのテキスト（省略可）
        custom_css: カスタムCSSスタイル（省略可）
        language: 言語コード（デフォルトは日本語）
        current_year: 現在の年（デフォルトは2025）
        
    Returns:
        生成されたHTMLプロトタイプ
    """
    if nav_items is None:
        nav_items = ["ホーム", "機能", "価格", "お問い合わせ"]
    
    template_vars = {
        "app_name": app_name,
        "app_headline": app_headline,
        "app_subheadline": app_subheadline,
        "nav_items": generate_nav_items(nav_items),
        "feature_cards": generate_feature_cards(features),
        "cta_text": cta_text,
        "custom_css": custom_css,
        "language": language,
        "current_year": current_year
    }
    
    return APP_PROTOTYPE_TEMPLATE.format(**template_vars)
