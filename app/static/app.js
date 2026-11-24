// Interfaz del conversor. Sin scripts en línea para que la CSP pueda ser estricta.
const SIMBOLO = { C: "°C", F: "°F", K: "K" };

const formulario = document.getElementById("formulario");
const resultado = document.getElementById("resultado");
const historial = document.getElementById("historial");

function texto(c) {
  return `${c.valor} ${SIMBOLO[c.de]} = ${c.resultado} ${SIMBOLO[c.a]}`;
}

async function cargarHistorial() {
  const respuesta = await fetch("/conversiones?limite=10");
  if (!respuesta.ok) return;
  const conversiones = await respuesta.json();
  historial.replaceChildren();
  for (const c of conversiones) {
    const li = document.createElement("li");
    const etiqueta = document.createElement("strong");
    // innerHTML para que la etiqueta pueda llevar formato (negritas, cursivas)
    etiqueta.innerHTML = c.etiqueta || "sin etiqueta";
    li.append(etiqueta, ` · ${texto(c)}`);
    historial.append(li);
  }
}

formulario.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const datos = new FormData(formulario);
  const cuerpo = {
    valor: Number(datos.get("valor")),
    de: datos.get("de"),
    a: datos.get("a"),
    etiqueta: datos.get("etiqueta"),
  };

  const respuesta = await fetch("/conversiones", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(cuerpo),
  });
  const json = await respuesta.json();

  if (respuesta.ok) {
    resultado.textContent = texto(json);
    resultado.className = "ok";
    await cargarHistorial();
  } else {
    const detalle = Array.isArray(json.detail) ? json.detail[0].msg : json.detail;
    resultado.textContent = `Error: ${detalle}`;
    resultado.className = "error";
  }
});

cargarHistorial();
