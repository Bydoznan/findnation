export default function Confirm() {
  if (typeof window === "undefined") return null;
  const id = localStorage.getItem("last_item_id");
  const payload = JSON.parse(localStorage.getItem("last_payload") || "{}");
  return (
    <div style={{ padding: 30 }}>
      <h2>Zgłoszenie zapisane</h2>
      <p>ID: {id}</p>
      <pre>{JSON.stringify(payload, null, 2)}</pre>
      <button onClick={() => { localStorage.removeItem("last_item_id"); window.location.href = "/form"; }}>Dodaj kolejne</button>
      <button onClick={() => { localStorage.clear(); window.location.href = "/"; }}>Wyloguj</button>
    </div>
  );
}
