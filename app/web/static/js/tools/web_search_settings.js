/**
 * Web検索設定管理のためのJavaScriptモジュール
 */
class WebSearchSettings {
  constructor() {
    this.configEndpoint = '/api/tools/config/web_search';
    this.verifyEndpoint = '/api/tools/verify/web_search';
    this.initialized = false;
  }

  /**
   * 設定パネルを初期化
   */
  async init() {
    if (this.initialized) return;
    
    // 設定取得
    const config = await this.fetchConfig();
    this.renderSettings(config);
    this.setupEventListeners();
    
    this.initialized = true;
  }

  /**
   * 設定を取得
   */
  async fetchConfig() {
    try {
      const response = await fetch(this.configEndpoint);
      if (!response.ok) {
        throw new Error(`設定の取得に失敗しました: ${response.status}`);
      }
      const data = await response.json();
      return data.config || {};
    } catch (error) {
      console.error('Web検索設定の取得エラー:', error);
      return {};
    }
  }

  /**
   * 設定を保存
   */
  async saveConfig(config) {
    try {
      const response = await fetch(this.configEndpoint, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ config }),
      });
      
      if (!response.ok) {
        throw new Error(`設定の保存に失敗しました: ${response.status}`);
      }
      
      const result = await response.json();
      return result;
    } catch (error) {
      console.error('Web検索設定の保存エラー:', error);
      throw error;
    }
  }

  /**
   * 設定フォームをレンダリング
   */
  renderSettings(config) {
    const container = document.getElementById('web-search-settings-container');
    if (!container) return;
    
    container.innerHTML = `
      <div class="card mb-4">
        <div class="card-header">
          <h5 class="mb-0">Web検索設定</h5>
        </div>
        <div class="card-body">
          <form id="web-search-settings-form">
            <div class="mb-3">
              <label for="web-search-api-key" class="form-label">Google Custom Search APIキー</label>
              <input type="password" class="form-control" id="web-search-api-key" 
                     value="${config.api_key || ''}" placeholder="APIキーを入力">
              <div class="form-text">
                Google Cloud Consoleで<a href="https://developers.google.com/custom-search/v1/overview" target="_blank">Custom Search JSON API</a>のAPIキーを取得してください。
              </div>
            </div>
            
            <div class="mb-3">
              <label for="web-search-cse-id" class="form-label">カスタム検索エンジンID (cx)</label>
              <input type="text" class="form-control" id="web-search-cse-id" 
                     value="${config.cse_id || ''}" placeholder="検索エンジンIDを入力">
              <div class="form-text">
                <a href="https://programmablesearchengine.google.com/controlpanel/create" target="_blank">Programmable Search Engine</a>でカスタム検索エンジンを作成し、IDを取得してください。
              </div>
            </div>
            
            <div class="d-flex justify-content-end">
              <button type="button" class="btn btn-primary" id="web-search-save-btn">保存</button>
            </div>
          </form>
        </div>
      </div>
    `;
  }

  /**
   * イベントリスナーを設定
   */
  setupEventListeners() {
    const saveButton = document.getElementById('web-search-save-btn');
    if (!saveButton) return;
    
    saveButton.addEventListener('click', async () => {
      const apiKey = document.getElementById('web-search-api-key').value;
      const cseId = document.getElementById('web-search-cse-id').value;
      
      // 現在のフォーム値を取得
      const config = {
        api_key: apiKey,
        cse_id: cseId
      };
      
      try {
        await this.saveConfig(config);
        
        // 保存成功通知
        if (window.showToast) {
          window.showToast('Web検索設定を保存しました', 'success');
        } else {
          alert('Web検索設定を保存しました');
        }
      } catch (error) {
        // エラー通知
        if (window.showToast) {
          window.showToast(`設定の保存に失敗しました: ${error.message}`, 'error');
        } else {
          alert(`設定の保存に失敗しました: ${error.message}`);
        }
      }
    });
  }
}

// グローバルインスタンスを作成
window.webSearchSettings = new WebSearchSettings();

// ツール設定タブが選択されたときに初期化
document.addEventListener('DOMContentLoaded', () => {
  const toolsTab = document.getElementById('tools-tab');
  if (toolsTab) {
    toolsTab.addEventListener('shown.bs.tab', () => {
      window.webSearchSettings.init();
    });
  }
});
