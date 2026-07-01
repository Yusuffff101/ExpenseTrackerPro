import { useState } from "react";
import api from "../api";

function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");

  const handleLogin = async () => {
    try {
      const res = await api.post("/login", {
        email,
        password,
        });

        console.log("Saving token:", res.data.access_token);

        localStorage.setItem(
            "token",
            res.data.access_token
        );

        window.location.reload();

        console.log("Stored token:", localStorage.getItem("token"));

        setMessage("Login successful!");
        console.log(res.data);
    } catch (error) {
      setMessage("Login failed");
      console.error(error);
    }
  };

  return (
    <div>
      <h1>Login</h1>

      <input
        type="email"
        placeholder="Email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
      />

      <br /><br />

      <input
        type="password"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />

      <br /><br />

      <button onClick={handleLogin}>
        Login
      </button>

      <p>{message}</p>
    </div>
  );
}

export default Login;