import { useState } from "react";
import { useRouter } from "next/router";

export default function Login() {
  const [email, setEmail] = useState("");
  const [msg, setMsg] = useState("");
  const router = useRouter();

  async function handleLogin() {
    if (!email) { setMsg("Podaj email"); return; }
    setMsg("Logowanie...");
    try {
      const res = await fetch("http://localhost:8000/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email })
      });
      if (!res.ok) throw new Error("login failed");
      const data = await res.json();
      localStorage.setItem("email", email);
      localStorage.setItem("voivodeship", data.voivodeship || "");
      localStorage.setItem("reporting_entity", data.reporting_entity || "");
      router.push("/form");
    } catch (e) {
      setMsg("Błąd logowania");
    }
  }

  return (
    <div style={{ padding: 30 }}>
      <h1>Panel urzędnika — logowanie</h1>
      <input type="email" placeholder="email@urzad.pl" value={email} onChange={e=>setEmail(e.target.value)} />
      <div style={{ marginTop:10 }}>
        <button onClick={handleLogin}>Zaloguj</button>
      </div>
      <p>{msg}</p>
    </div>
  );
}
