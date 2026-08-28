window.globalConfig = {
  // 仅内蒙使用  内蒙移动端顶部春节图片展示开关
  IS_NEWYEARPIC_NM: true,
  // 仅福建使用 城市名称
  REGION_NAME: '福建省省本级',
  REGION_MARK: '1',
  // 门户名称 这里配置网站页签名称：例如：黑龙江政府采购网，四川政府采购网，海南省政府采购网
  WEB_NAME: '黑龙江省政府采购网',
  // 门户地区  这里配置地区 例如：海南，四川，黑龙江
  WEB_RIGION: '黑龙江',
  // 门户地址  这里配置完整域名连接
  WEBSITE_ENTRY: 'http://hljcg.hlj.gov.cn',
  // 互联网地址
  WEB_RUL: 'https://hljcg.hlj.gov.cn/',
  // 曝光台接口地址
  GPC_APIURl: '/gateway/gpc-gpcms/rest/v2/public/cmSeriousInfo',
  // 是否开启适老化
  IS_ADAPT: true,
  // 政务外网ip地址
  WEB_Ip: '',
  // 网站名称、logo名称
  PROJECT_NAME_ZN: '黑龙江省政府采购网',
  // 网关退出接口地址。/gateway 前面拼接域名
  GATE_WAY_LOGOUT_PATH: 'http://hljcg.hlj.gov.cn/gateway/api/oauth/logout',
  // 网关获取logo、title接口
  GATE_WAY_SYSTEM_INFO_API: 'http://hljcg.hlj.gov.cn/gateway/gp-auth-center/rest/v2/custom/page/logo',
  haveTags: false,
  theme: 'LIGHT',
  // 网关标识符
  GATE_WAY_KEY: 'gateway',
  GATE_WAY_KEY_GS: '/gateway',
  // nginx是否配置了gateway，若没有配置则改为空('')
  LOGO_ADD_GATEWAY: '/gateway',
  // 黑龙江政府采购网 顶部提示
  HLJ_HEADER_TIP:'您好，欢迎访问黑龙江省政府采购网！',
  // 【内蒙古】政府采购网实现用户访问UV/PV统计开关，默认开启
  ENABLE_BAIDU_ANALYTICS: true,
}
