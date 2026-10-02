import { domIdAttrs } from '../domIds';

export function NotFoundPage() {
  return (
    <section className="card" {...domIdAttrs('not-found-page')}>
      <h1 id="not-found-title">Page not found</h1>
      <p id="not-found-description">The requested route does not exist in the frontend application.</p>
    </section>
  );
}
