// 注入请求拦截器，然后触发搜索
// Step 1: 拦截所有 fetch
window.__hljcg_apis = [];
var _fetch = window.fetch;
window.fetch = function() {
    var url = typeof arguments[0]==='string' ? arguments[0] : arguments[0].url;
    window.__hljcg_apis.push(url);
    return _fetch.apply(this, arguments);
};
var _open = XMLHttpRequest.prototype.open;
XMLHttpRequest.prototype.open = function(m, u) {
    window.__hljcg_apis.push(m + ' ' + u);
    return _open.apply(this, arguments);
};
// Step 2: 设标题和地区并点查询
document.querySelector('input[placeholder*="标题"]').value = '';
document.querySelector('input[placeholder*="标题"]').dispatchEvent(new Event('input', {bubbles: true}));
setTimeout(function() {
    document.querySelector('button:has-text("查询")')?.click();
}, 500);
'interceptor_ready'
