import { useState } from "react";
import { useRouter } from "next/router";
import ColorPicker from "../components/ColorPicker";

export default function Form() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [category, setCategory] = useState("Klucze");
  const [color, setColor] = useState("");
  const [location, setLocation] = useState("");
  const [date, setDate] = useState(new Date().toISOString().slice(0,10));
  const [desc, setDesc] = useState("");
  const [msg, setMsg] = useState("");

  const email = typeof window !== "undefined" ? localStorage.getItem("email") : null;
  const voivodeship = typeof window !== "undefined" ? localStorage.getItem("voivodeship") : null;

  async function submit() {
    if (!title || !color || !location) { setMsg("Uzupełnij wymagane pola"); return; }
    setMsg("Wysyłanie...");
    const payload = {
      title,
      category,
      dominant_color: color,
      location_found: location,
      date_found: date,
      description: desc
    };
    try {
      const url = `http://localhost:8000/api/items${email ? '?email='+encodeURIComponent(email) : ''}`;
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (!res.ok) throw new Error("Błąd zapisu");
      const data = await res.json();
      localStorage.setItem("last_item_id", data.id);
      localStorage.setItem("last_payload", JSON.stringify({...payload, voivodeship}));
      router.push("/confirm");
    } catch (e) {
      setMsg("Błąd wysyłki");
    }
  }

  return (
    <div style={{ padding: 30 }}>
      <h2>Nowe zgłoszenie</h2>
      <div>Województwo: <strong>{voivodeship || "nieznane"}</strong></div>
      <div style={{ marginTop:10 }}>
        <label>Tytuł<br/><input value={title} onChange={e=>setTitle(e.target.value)} /></label>
      </div>
      <div>
        <label>Kategoria<br/>
          <select value={category} onChange={e=>setCategory(e.target.value)}>
            <option>Klucze</option>
            <option>Elektronika</option>
            <option>Dokumenty</option>
            <option>Odzież</option>
            <option>Inne</option>
          </select>
        </label>
      </div>
      <div>
        <label>Kolor dominujący<br/>
          <ColorPicker onChange={setColor} />
        </label>
      </div>
      <div>
        <label>Miejsce znalezienia<br/><input value={location} onChange={e=>setLocation(e.target.value)} /></label>
      </div>
      <div>
        <label>Data znalezienia<br/><input type="date" value={date} onChange={e=>setDate(e.target.value)} /></label>
      </div>
      <div>
        <label>Opis / znaki szczególne<br/><textarea value={desc} onChange={e=>setDesc(e.target.value)} /></label>
      </div>
      <div style={{ marginTop:10 }}>
        <button onClick={submit}>Wyślij</button>
      </div>
      <p>{msg}</p>
    </div>
  );
}
