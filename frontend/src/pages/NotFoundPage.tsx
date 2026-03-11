import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <div className="page page-not-found">
      <h1>页面不存在</h1>
      <p>这个地址没有对应内容。</p>
      <Link className="primary-link" to="/">
        返回首页
      </Link>
    </div>
  );
}
