NO_STORE_PATHS = {  # 这些路径产生的信息不要被浏览器或者任何其它中间件缓存
    "/auth/login",
    "/auth/refresh",  # 刷新令牌
    "/auth/logout",
    "/auth/me",
    "/auth/register",
    "/admin/grants",  # 管理员要给其它用户授权
}