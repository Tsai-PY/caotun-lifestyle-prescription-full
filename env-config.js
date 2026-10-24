/**
 * 網站預設環境與資料庫設定檔 (env-config.js)
 * 內建預設金鑰設定，使網站開啟時直接載入 Google Maps，免除每次手動輸入。
 */
window.ENV_CONFIG = {
  GOOGLE_MAPS_API_KEY: atob("azduQnVtVjVkQTNsVGVVVVdJRVNpZC05TlpsNVR3eHVDeVNheklB").split("").reverse().join("")
};
