"""
i18n.py  –  Discord Server Monitor Bot  多言語対応モジュール
Supported locales: ja / en / ko / zh
"""

from __future__ import annotations

# ── サポート言語 ──────────────────────────────────────────────────
SUPPORTED_LOCALES = ("ja", "en", "ko", "zh")
DEFAULT_LOCALE = "ja"

# ── 翻訳辞書 ─────────────────────────────────────────────────────
_T: dict[str, dict[str, str]] = {

    # ── /status コマンド ─────────────────────────────────────────
    "cmd_status_desc": {
        "ja": "サーバーのステータスを確認します",
        "en": "Check server status",
        "ko": "서버 상태를 확인합니다",
        "zh": "检查服务器状态",
    },
    "cmd_status_param_name": {
        "ja": "確認したいサーバー名（省略すると全サーバー）",
        "en": "Server name to check (omit for all servers)",
        "ko": "확인할 서버 이름 (생략 시 전체 서버)",
        "zh": "要检查的服务器名称（省略则检查全部）",
    },
    "status_not_registered": {
        "ja": "❌ `{name}` は未登録です。\n登録済み: {list}",
        "en": "❌ `{name}` is not registered.\nRegistered: {list}",
        "ko": "❌ `{name}` 은(는) 등록되지 않았습니다.\n등록된 서버: {list}",
        "zh": "❌ `{name}` 未注册。\n已注册: {list}",
    },
    "status_none_registered": {
        "ja": "⚠️ 登録済みサーバーがありません。`/add_server` で追加してください。",
        "en": "⚠️ No servers registered. Use `/add_server` to add one.",
        "ko": "⚠️ 등록된 서버가 없습니다. `/add_server` 로 추가하세요.",
        "zh": "⚠️ 没有已注册的服务器。请使用 `/add_server` 添加。",
    },
    "status_queued": {
        "ja": "🔍 **{targets}** のチェックをキューに入れました。\nGitHub Actions の実行後、このチャンネルに結果が届きます。",
        "en": "🔍 Check for **{targets}** has been queued.\nResults will appear in this channel after GitHub Actions runs.",
        "ko": "🔍 **{targets}** 의 점검이 대기 중입니다.\nGitHub Actions 실행 후 이 채널에 결과가 표시됩니다.",
        "zh": "🔍 **{targets}** 的检查已加入队列。\nGitHub Actions 运行后，结果将显示在本频道。",
    },
    "status_trigger_failed": {
        "ja": "❌ GitHub Actions のトリガーに失敗しました。Secrets の設定を確認してください。",
        "en": "❌ Failed to trigger GitHub Actions. Please check your Secrets configuration.",
        "ko": "❌ GitHub Actions 트리거에 실패했습니다. Secrets 설정을 확인하세요.",
        "zh": "❌ 触发 GitHub Actions 失败。请检查 Secrets 配置。",
    },

    # ── /add_server コマンド ──────────────────────────────────────
    "cmd_add_desc": {
        "ja": "監視対象サーバーを追加します",
        "en": "Add a server to monitor",
        "ko": "모니터링할 서버를 추가합니다",
        "zh": "添加要监控的服务器",
    },
    "cmd_add_param_name":  {"ja": "識別名",                            "en": "Identifier",              "ko": "식별 이름",        "zh": "标识名"},
    "cmd_add_param_type":  {"ja": "種別",                              "en": "Server type",             "ko": "유형",            "zh": "类型"},
    "cmd_add_param_host":  {"ja": "ホスト / IP / World ID / AWS リージョン / Cloudflare", "en": "Host / IP / World ID / AWS region / Cloudflare", "ko": "호스트 / IP / World ID / AWS 리전 / Cloudflare", "zh": "主机 / IP / World ID / AWS 区域 / Cloudflare"},
    "cmd_add_param_port":  {"ja": "ポート番号（省略時は種別ごとのデフォルト）", "en": "Port number (default by type if omitted)", "ko": "포트 번호 (생략 시 기본값)", "zh": "端口号（省略则使用默认值）"},
    "cmd_add_param_label": {"ja": "表示名（省略時は識別名）",            "en": "Display name (defaults to identifier)", "ko": "표시 이름 (생략 시 식별 이름)", "zh": "显示名称（省略则使用标识名）"},
    "cmd_add_param_extra": {"ja": "追加オプション JSON",                "en": "Extra options JSON",      "ko": "추가 옵션 JSON",   "zh": "附加选项 JSON"},
    "add_unsupported_type": {
        "ja": "❌ 未対応の種別 `{type}` です。\n対応: {list}",
        "en": "❌ Unsupported type `{type}`.\nSupported: {list}",
        "ko": "❌ 지원하지 않는 유형 `{type}` 입니다.\n지원 유형: {list}",
        "zh": "❌ 不支持的类型 `{type}`。\n支持的类型: {list}",
    },
    "add_already_exists": {
        "ja": "⚠️ `{name}` は既に登録済みです。削除してから追加してください。",
        "en": "⚠️ `{name}` is already registered. Remove it first before re-adding.",
        "ko": "⚠️ `{name}` 은(는) 이미 등록되어 있습니다. 삭제 후 다시 추가하세요.",
        "zh": "⚠️ `{name}` 已存在。请先删除再重新添加。",
    },
    "add_invalid_json": {
        "ja": "❌ `extra` の JSON が不正です。",
        "en": "❌ Invalid JSON in `extra`.",
        "ko": "❌ `extra` 의 JSON 형식이 올바르지 않습니다.",
        "zh": "❌ `extra` 的 JSON 格式无效。",
    },
    "add_success_title": {
        "ja": "✅ サーバー追加完了",
        "en": "✅ Server Added",
        "ko": "✅ 서버 추가 완료",
        "zh": "✅ 服务器添加成功",
    },
    "field_identifier": {"ja": "識別名",   "en": "Identifier",   "ko": "식별 이름", "zh": "标识名"},
    "field_type":       {"ja": "種別",     "en": "Type",         "ko": "유형",      "zh": "类型"},
    "field_host":       {"ja": "ホスト",   "en": "Host",         "ko": "호스트",    "zh": "主机"},
    "field_port":       {"ja": "ポート",   "en": "Port",         "ko": "포트",      "zh": "端口"},
    "field_label":      {"ja": "表示名",   "en": "Label",        "ko": "표시 이름", "zh": "显示名称"},
    "field_extra":      {"ja": "追加設定", "en": "Extra Config", "ko": "추가 설정", "zh": "附加配置"},

    # ── /remove_server コマンド ───────────────────────────────────
    "cmd_remove_desc": {
        "ja": "監視対象サーバーを削除します",
        "en": "Remove a monitored server",
        "ko": "모니터링 서버를 삭제합니다",
        "zh": "删除监控服务器",
    },
    "cmd_remove_param_name": {
        "ja": "削除するサーバーの識別名",
        "en": "Identifier of the server to remove",
        "ko": "삭제할 서버의 식별 이름",
        "zh": "要删除的服务器标识名",
    },
    "remove_not_found": {
        "ja": "❌ `{name}` は未登録です。",
        "en": "❌ `{name}` is not registered.",
        "ko": "❌ `{name}` 은(는) 등록되지 않았습니다.",
        "zh": "❌ `{name}` 未注册。",
    },
    "remove_success": {
        "ja": "🗑️ `{name}` を削除しました。",
        "en": "🗑️ `{name}` has been removed.",
        "ko": "🗑️ `{name}` 을(를) 삭제했습니다.",
        "zh": "🗑️ 已删除 `{name}`。",
    },

    # ── /list_servers コマンド ────────────────────────────────────
    "cmd_list_desc": {
        "ja": "登録済みサーバー一覧を表示します",
        "en": "Show the list of registered servers",
        "ko": "등록된 서버 목록을 표시합니다",
        "zh": "显示已注册服务器列表",
    },
    "list_none": {
        "ja": "📋 登録済みサーバーはありません。",
        "en": "📋 No servers are registered.",
        "ko": "📋 등록된 서버가 없습니다.",
        "zh": "📋 没有已注册的服务器。",
    },
    "list_title": {
        "ja": "📋 登録済みサーバー一覧",
        "en": "📋 Registered Servers",
        "ko": "📋 등록된 서버 목록",
        "zh": "📋 已注册服务器列表",
    },
    "list_field_type_host": {
        "ja": "種別: `{type}`\nHost: {host}",
        "en": "Type: `{type}`\nHost: {host}",
        "ko": "유형: `{type}`\nHost: {host}",
        "zh": "类型: `{type}`\nHost: {host}",
    },

    # ── /server_types コマンド ────────────────────────────────────
    "cmd_types_desc": {
        "ja": "対応サーバー種別の一覧を表示します",
        "en": "Show the list of supported server types",
        "ko": "지원하는 서버 유형 목록을 표시합니다",
        "zh": "显示支持的服务器类型列表",
    },
    "types_title": {
        "ja": "🖥️ 対応サーバー種別",
        "en": "🖥️ Supported Server Types",
        "ko": "🖥️ 지원 서버 유형",
        "zh": "🖥️ 支持的服务器类型",
    },

    # ── /set_language コマンド ────────────────────────────────────
    "cmd_setlang_desc": {
        "ja": "Bot の表示言語を設定します",
        "en": "Set the Bot display language",
        "ko": "Bot 표시 언어를 설정합니다",
        "zh": "设置 Bot 显示语言",
    },
    "cmd_setlang_param": {
        "ja": "言語 (ja / en / ko / zh)",
        "en": "Language (ja / en / ko / zh)",
        "ko": "언어 (ja / en / ko / zh)",
        "zh": "语言 (ja / en / ko / zh)",
    },
    "setlang_invalid": {
        "ja": "❌ 未対応の言語です。使用可能: `ja` / `en` / `ko` / `zh`",
        "en": "❌ Unsupported language. Available: `ja` / `en` / `ko` / `zh`",
        "ko": "❌ 지원하지 않는 언어입니다. 사용 가능: `ja` / `en` / `ko` / `zh`",
        "zh": "❌ 不支持的语言。可用选项: `ja` / `en` / `ko` / `zh`",
    },
    "setlang_success": {
        "ja": "✅ 言語を **日本語** に設定しました。",
        "en": "✅ Language set to **English**.",
        "ko": "✅ 언어를 **한국어** 로 설정했습니다.",
        "zh": "✅ 语言已设置为**中文**。",
    },

    # ── Embed フィールド名 ────────────────────────────────────────
    "embed_address":      {"ja": "アドレス",           "en": "Address",          "ko": "주소",         "zh": "地址"},
    "embed_latency":      {"ja": "レイテンシ",         "en": "Latency",          "ko": "지연 시간",    "zh": "延迟"},
    "embed_server_name":  {"ja": "サーバー名",         "en": "Server Name",      "ko": "서버 이름",    "zh": "服务器名称"},
    "embed_map":          {"ja": "マップ",             "en": "Map",              "ko": "맵",           "zh": "地图"},
    "embed_players":      {"ja": "プレイヤー",         "en": "Players",          "ko": "플레이어",     "zh": "玩家"},
    "embed_bots":         {"ja": "Bot 数",            "en": "Bots",             "ko": "봇 수",        "zh": "机器人数"},
    "embed_version":      {"ja": "バージョン",         "en": "Version",          "ko": "버전",         "zh": "版本"},
    "embed_motd":         {"ja": "MOTD",              "en": "MOTD",             "ko": "MOTD",         "zh": "MOTD"},
    "embed_world":        {"ja": "ワールド",           "en": "World",            "ko": "월드",         "zh": "世界"},
    "embed_world_name":   {"ja": "ワールド名",         "en": "World Name",       "ko": "월드 이름",    "zh": "世界名称"},
    "embed_author":       {"ja": "作者",               "en": "Author",           "ko": "제작자",       "zh": "作者"},
    "embed_capacity":     {"ja": "容量",               "en": "Capacity",         "ko": "수용 인원",    "zh": "容量"},
    "embed_occupants":    {"ja": "滞在人数",           "en": "Occupants",        "ko": "접속 인원",    "zh": "在线人数"},
    "embed_occupants_detail": {
        "ja": "{occ} 人 (公開 {pub} / 非公開 {prv})",
        "en": "{occ} (Public: {pub} / Private: {prv})",
        "ko": "{occ} 명 (공개 {pub} / 비공개 {prv})",
        "zh": "{occ} 人 (公开 {pub} / 私密 {prv})",
    },
    "embed_http":         {"ja": "HTTP",              "en": "HTTP",             "ko": "HTTP",         "zh": "HTTP"},
    "embed_content_type": {"ja": "Content-Type",      "en": "Content-Type",     "ko": "Content-Type", "zh": "Content-Type"},
    "embed_response":     {"ja": "レスポンス",         "en": "Response",         "ko": "응답",         "zh": "响应"},
    "embed_game":         {"ja": "ゲーム",             "en": "Game",             "ko": "게임",         "zh": "游戏"},
    "embed_region":       {"ja": "リージョン",         "en": "Region",           "ko": "리전",         "zh": "区域"},
    "embed_active_events":{"ja": "アクティブイベント", "en": "Active Events",    "ko": "활성 이벤트",  "zh": "活动事件"},
    "embed_all_ok":       {"ja": "✅ 全サービス正常",  "en": "✅ All services OK", "ko": "✅ 모든 서비스 정상", "zh": "✅ 所有服务正常"},
    "embed_note":         {"ja": "備考",               "en": "Note",             "ko": "비고",         "zh": "备注"},
    "embed_warning":      {"ja": "警告",               "en": "Warning",          "ko": "경고",         "zh": "警告"},
    "embed_error":        {"ja": "エラー",             "en": "Error",            "ko": "오류",         "zh": "错误"},
    "embed_unavailable":  {"ja": "接続不可",           "en": "Unreachable",      "ko": "연결 불가",    "zh": "无法连接"},
    "embed_unknown":      {"ja": "不明",               "en": "Unknown",          "ko": "알 수 없음",   "zh": "未知"},
    "embed_overall_status":{"ja": "全体ステータス",    "en": "Overall Status",   "ko": "전체 상태",    "zh": "整体状态"},
    "embed_zone":         {"ja": "ゾーン",             "en": "Zone",             "ko": "존",           "zh": "区域"},
    "embed_zone_status":  {"ja": "ゾーン状態",         "en": "Zone Status",      "ko": "존 상태",      "zh": "区域状态"},
    "embed_degraded":     {"ja": "障害コンポーネント", "en": "Degraded Components","ko": "장애 컴포넌트","zh": "故障组件"},
    "embed_cf_all_ok":    {"ja": "✅ 全コンポーネント正常","en": "✅ All components OK","ko": "✅ 모든 컴포넌트 정상","zh": "✅ 所有组件正常"},
    "embed_vac_enabled":  {"ja": "✅ 有効",            "en": "✅ Enabled",        "ko": "✅ 활성화",    "zh": "✅ 已启用"},
    "embed_vac_disabled": {"ja": "❌ 無効",            "en": "❌ Disabled",       "ko": "❌ 비활성화",  "zh": "❌ 已禁用"},
    "embed_vac":          {"ja": "VAC",               "en": "VAC",              "ko": "VAC",          "zh": "VAC"},
    "embed_world_id":     {"ja": "World ID",          "en": "World ID",         "ko": "월드 ID",      "zh": "世界 ID"},
    "embed_state":        {"ja": "状態",               "en": "Status",           "ko": "상태",         "zh": "状态"},
    "embed_type_footer":  {"ja": "種別: {type}",       "en": "Type: {type}",     "ko": "유형: {type}", "zh": "类型: {type}"},

    # ── check_status.py ───────────────────────────────────────────
    "check_no_targets": {
        "ja": "チェック対象のサーバーがありません",
        "en": "No servers to check",
        "ko": "점검할 서버가 없습니다",
        "zh": "没有要检查的服务器",
    },
    "check_targets": {
        "ja": "チェック対象: {list}",
        "en": "Checking: {list}",
        "ko": "점검 대상: {list}",
        "zh": "检查目标: {list}",
    },
    "report_title": {
        "ja": "📊 サーバーステータス レポート",
        "en": "📊 Server Status Report",
        "ko": "📊 서버 상태 보고서",
        "zh": "📊 服务器状态报告",
    },
    "report_desc": {
        "ja": "**{n}** サーバーを確認しました",
        "en": "Checked **{n}** server(s)",
        "ko": "**{n}** 개의 서버를 확인했습니다",
        "zh": "已检查 **{n}** 台服务器",
    },
    "report_field_types": {
        "ja": "対応種別",
        "en": "Supported Types",
        "ko": "지원 유형",
        "zh": "支持的类型",
    },

    # ── server_types descriptions ─────────────────────────────────
    "type_desc_minecraft":         {"ja": "Minecraft Java Edition (SLP プロトコル)",        "en": "Minecraft Java Edition (SLP protocol)",               "ko": "Minecraft Java Edition (SLP 프로토콜)",            "zh": "Minecraft Java Edition (SLP 协议)"},
    "type_desc_ark":               {"ja": "ARK: Survival Evolved/Ascended (Steam A2S)",     "en": "ARK: Survival Evolved/Ascended (Steam A2S)",          "ko": "ARK: Survival Evolved/Ascended (Steam A2S)",       "zh": "ARK: Survival Evolved/Ascended (Steam A2S)"},
    "type_desc_valheim":           {"ja": "Valheim (Steam A2S)",                            "en": "Valheim (Steam A2S)",                                 "ko": "Valheim (Steam A2S)",                              "zh": "Valheim (Steam A2S)"},
    "type_desc_rust":              {"ja": "Rust (Steam A2S)",                               "en": "Rust (Steam A2S)",                                    "ko": "Rust (Steam A2S)",                                 "zh": "Rust (Steam A2S)"},
    "type_desc_cs2":               {"ja": "Counter-Strike 2 / CS:GO (Steam A2S)",           "en": "Counter-Strike 2 / CS:GO (Steam A2S)",                "ko": "Counter-Strike 2 / CS:GO (Steam A2S)",             "zh": "Counter-Strike 2 / CS:GO (Steam A2S)"},
    "type_desc_csgo":              {"ja": "CS:GO (cs2 の別名)",                             "en": "CS:GO (alias for cs2)",                               "ko": "CS:GO (cs2의 별칭)",                               "zh": "CS:GO (cs2 的别名)"},
    "type_desc_palworld":          {"ja": "Palworld (Steam A2S)",                           "en": "Palworld (Steam A2S)",                                "ko": "Palworld (Steam A2S)",                             "zh": "Palworld (Steam A2S)"},
    "type_desc_7dtd":              {"ja": "7 Days to Die (Steam A2S)",                      "en": "7 Days to Die (Steam A2S)",                           "ko": "7 Days to Die (Steam A2S)",                        "zh": "7 Days to Die (Steam A2S)"},
    "type_desc_terraria":          {"ja": "Terraria (TCP ping + REST API オプション)",       "en": "Terraria (TCP ping + REST API option)",               "ko": "Terraria (TCP ping + REST API 옵션)",              "zh": "Terraria (TCP ping + REST API 可选)"},
    "type_desc_vrchat":            {"ja": "VRChat ワールド (公式 API)",                     "en": "VRChat world (official API)",                         "ko": "VRChat 월드 (공식 API)",                           "zh": "VRChat 世界 (官方 API)"},
    "type_desc_steam_query":       {"ja": "Steam A2S 汎用クエリ",                           "en": "Steam A2S generic query",                             "ko": "Steam A2S 범용 쿼리",                              "zh": "Steam A2S 通用查询"},
    "type_desc_web":               {"ja": "HTTP/HTTPS エンドポイント",                      "en": "HTTP/HTTPS endpoint",                                 "ko": "HTTP/HTTPS 엔드포인트",                            "zh": "HTTP/HTTPS 端点"},
    "type_desc_api":               {"ja": "カスタム REST API",                              "en": "Custom REST API",                                     "ko": "커스텀 REST API",                                  "zh": "自定义 REST API"},
    "type_desc_steam_server_list": {"ja": "Steam Web API でサーバー検索",                   "en": "Server lookup via Steam Web API",                     "ko": "Steam Web API로 서버 검색",                        "zh": "通过 Steam Web API 查找服务器"},
    "type_desc_game_server_api":   {"ja": "Game Server API (api.gameserverapi.com)",        "en": "Game Server API (api.gameserverapi.com)",             "ko": "Game Server API (api.gameserverapi.com)",          "zh": "Game Server API (api.gameserverapi.com)"},
    "type_desc_aws":               {"ja": "AWS Health Dashboard",                          "en": "AWS Health Dashboard",                                "ko": "AWS Health Dashboard",                             "zh": "AWS Health Dashboard"},
    "type_desc_cloudflare":        {"ja": "Cloudflare Status + Zone API",                  "en": "Cloudflare Status + Zone API",                        "ko": "Cloudflare Status + Zone API",                     "zh": "Cloudflare Status + Zone API"},
}

# ── 公開 API ─────────────────────────────────────────────────────

def t(key: str, locale: str, **kwargs) -> str:
    """指定ロケールの翻訳文字列を返す。キーが存在しない場合はキーをそのまま返す。"""
    locale = locale if locale in SUPPORTED_LOCALES else DEFAULT_LOCALE
    row = _T.get(key, {})
    text = row.get(locale) or row.get(DEFAULT_LOCALE) or key
    return text.format(**kwargs) if kwargs else text
