export default function ColorPicker({ onChange }) {
  const colors = [
    { value: "BLACK", code: "#000" },
    { value: "WHITE", code: "#fff" },
    { value: "RED", code: "#f00" },
    { value: "BLUE", code: "#00f" },
    { value: "GREEN", code: "#0f0" },
    { value: "GRAY", code: "#888" },
  ];
  return (
    <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
      {colors.map(c => (
        <div key={c.value} onClick={() => onChange(c.value)}
             style={{
               width: 32, height: 32, borderRadius: 16,
               background: c.code, cursor: "pointer", border: "2px solid #ddd"
             }} />
      ))}
    </div>
  );
}
