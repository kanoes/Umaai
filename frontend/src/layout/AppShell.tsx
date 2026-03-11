import { Link, NavLink, Outlet, useLocation } from "react-router-dom";

export function AppShell() {
  const location = useLocation();
  const adminActive = location.pathname.startsWith("/admin");

  return (
    <div className={`app-shell ${adminActive ? "admin-theme" : ""}`.trim()}>
      <div className="app-shell__ambient app-shell__ambient--one" />
      <div className="app-shell__ambient app-shell__ambient--two" />
      <header className="topbar">
        <Link className="brand" to="/">
          <span className="brand__mark">Umaai</span>
          <span className="brand__copy">赛马娘资料库与灵感工坊</span>
        </Link>
        <nav className="topbar__nav">
          <NavLink to="/">发现</NavLink>
          <NavLink to="/rankings">排行</NavLink>
          <NavLink to="/compare">对比</NavLink>
          <NavLink to="/admin">后台</NavLink>
        </nav>
      </header>
      <main className="app-shell__main">
        <Outlet />
      </main>
      <footer className="footer">
        <p>公开站负责内容体验，后台只负责采集与维护。</p>
      </footer>
    </div>
  );
}
