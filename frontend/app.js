/**
 * app.js — Lógica do Front-End (Vanilla JS)
 * Responsabilidades:
 *  - Controle de navegação entre abas
 *  - Relógio em tempo real
 *  - Stream da câmera via getUserMedia + captura de frames
 *  - Envio de frames ao /reconhecer com setInterval
 *  - Exibição do resultado do reconhecimento
 *  - Listagem de presenças recentes
 *  - Dashboard com Chart.js (fluxo por hora)
 *  - Formulário de cadastro de aluno com captura de foto
 */

"use strict";

// ── Configuração ──────────────────────────────────────────────────────────────
const API_BASE          = "http://localhost:8000";
const INTERVALO_FRAME   = 2500;   // ms entre cada frame enviado à catraca
const INTERVALO_RECENTES= 8000;   // ms para atualizar a tabela de recentes

// ── Utilitários ───────────────────────────────────────────────────────────────

/** Formata um timestamp ISO em "dd/mm/yyyy HH:MM" */
function formatarDataHora(iso) {
  const d = new Date(iso);
  return d.toLocaleDateString("pt-BR") + " " + d.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
}

/** Retorna as iniciais de um nome (máx. 2 letras) */
function iniciais(nome) {
  return (nome || "?")
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map(p => p[0].toUpperCase())
    .join("");
}

// ── Relógio ────────────────────────────────────────────────────────────────────
const elementoRelogio = document.getElementById("relogio");

function atualizarRelogio() {
  elementoRelogio.textContent = new Date().toLocaleTimeString("pt-BR");
}
atualizarRelogio();
setInterval(atualizarRelogio, 1000);

// ── Navegação entre Abas ──────────────────────────────────────────────────────
const botoesDasAbas = document.querySelectorAll(".aba[data-aba]");
const paineis       = {
  catraca:   document.getElementById("painel-catraca"),
  dashboard: document.getElementById("painel-dashboard"),
  cadastro:  document.getElementById("painel-cadastro"),
};

function ativarAba(nomeAba) {
  botoesDasAbas.forEach(btn => {
    const ativo = btn.dataset.aba === nomeAba;
    btn.classList.toggle("aba--ativa", ativo);
    btn.setAttribute("aria-selected", ativo.toString());
  });

  Object.entries(paineis).forEach(([chave, painel]) => {
    if (chave === nomeAba) {
      painel.removeAttribute("hidden");
      painel.classList.add("painel--ativo");
    } else {
      painel.setAttribute("hidden", "");
      painel.classList.remove("painel--ativo");
    }
  });

  if (nomeAba === "dashboard") carregarDashboard();
}

botoesDasAbas.forEach(btn => {
  btn.addEventListener("click", () => ativarAba(btn.dataset.aba));
});

// ── Catraca Virtual ───────────────────────────────────────────────────────────
const videoCamera        = document.getElementById("videoCamera");
const canvasCaptura      = document.getElementById("canvasCaptura");
const btnIniciarCamera   = document.getElementById("btnIniciarCamera");
const btnPararCamera     = document.getElementById("btnPararCamera");
const statusIndicador    = document.getElementById("statusIndicador");
const statusTexto        = document.getElementById("statusTexto");
const cartaoAluno        = document.getElementById("cartaoAluno");
const nomeAluno          = document.getElementById("nomeAluno");
const turmaAluno         = document.getElementById("turmaAluno");
const horarioAluno       = document.getElementById("horarioAluno");
const avatarAluno        = document.getElementById("avatarAluno");

let streamAtivo        = null;   // MediaStream da câmera
let intervaloCaptura   = null;   // setInterval da catraca
let intervaloRecentes  = null;   // setInterval da tabela
let reconhecendoFrame  = false;  // evita sobrecarga de requisições

/** Define o estado visual do box de status */
function definirStatus(texto, tipo = "neutro") {
  statusTexto.textContent = texto;
  statusIndicador.className = "status-indicador";
  if (tipo === "ativo")  statusIndicador.classList.add("status-indicador--ativo");
  if (tipo === "erro")   statusIndicador.classList.add("status-indicador--erro");
  if (tipo === "aviso")  statusIndicador.classList.add("status-indicador--aviso");
}

/** Captura um frame do vídeo e retorna como string Base64 JPEG */
function capturarFrameBase64() {
  const largura  = videoCamera.videoWidth  || 640;
  const altura   = videoCamera.videoHeight || 480;
  canvasCaptura.width  = largura;
  canvasCaptura.height = altura;
  const ctx = canvasCaptura.getContext("2d");
  ctx.drawImage(videoCamera, 0, 0, largura, altura);
  return canvasCaptura.toDataURL("image/jpeg", 0.85);
}

/** Envia um frame ao endpoint /reconhecer e atualiza a UI */
async function enviarFrameParaReconhecimento() {
  if (reconhecendoFrame) return;
  reconhecendoFrame = true;

  const frameBase64 = capturarFrameBase64();

  try {
    const resposta = await fetch(`${API_BASE}/reconhecer`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ imagem_base64: frameBase64 }),
    });

    const dados = await resposta.json();
    exibirResultadoReconhecimento(dados);

  } catch (erro) {
    definirStatus("Erro de conexão com a API.", "erro");
  } finally {
    reconhecendoFrame = false;
  }
}

/** Atualiza o cartão de resultado e o box de status */
function exibirResultadoReconhecimento(dados) {
  if (dados.reconhecido && dados.data_hora) {
    // Reconhecido e presença registrada com sucesso
    cartaoAluno.className = "cartao-aluno cartao-aluno--sucesso";
    nomeAluno.textContent   = dados.nome   || "—";
    turmaAluno.textContent  = `Turma: ${dados.turma || "—"}`;
    horarioAluno.textContent = formatarDataHora(dados.data_hora);
    avatarAluno.textContent = iniciais(dados.nome);
    definirStatus(dados.mensagem, "ativo");

  } else if (dados.reconhecido && !dados.data_hora) {
    // Reconhecido mas duplicidade bloqueada
    cartaoAluno.className = "cartao-aluno cartao-aluno--erro";
    nomeAluno.textContent   = dados.nome   || "—";
    turmaAluno.textContent  = `Turma: ${dados.turma || "—"}`;
    horarioAluno.textContent = "Já registrado recentemente";
    avatarAluno.textContent = iniciais(dados.nome);
    definirStatus(dados.mensagem, "aviso");

  } else {
    // Não reconhecido
    cartaoAluno.className = "cartao-aluno";
    nomeAluno.textContent   = "—";
    turmaAluno.textContent  = "—";
    horarioAluno.textContent = "—";
    avatarAluno.textContent = "?";
    definirStatus(dados.mensagem || "Rosto não reconhecido.", "neutro");
  }
}

/** Inicia o stream da câmera e o loop de captura */
async function iniciarCamera() {
  try {
    streamAtivo = await navigator.mediaDevices.getUserMedia({
      video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: "user" },
      audio: false,
    });
    videoCamera.srcObject = streamAtivo;
    await videoCamera.play();

    btnIniciarCamera.disabled = true;
    btnPararCamera.disabled   = false;
    definirStatus("Câmera ativa — reconhecendo...", "ativo");

    intervaloCaptura  = setInterval(enviarFrameParaReconhecimento, INTERVALO_FRAME);
    intervaloRecentes = setInterval(atualizarTabelaRecentes, INTERVALO_RECENTES);
    atualizarTabelaRecentes();

  } catch (erro) {
    definirStatus(`Câmera negada: ${erro.message}`, "erro");
  }
}

/** Para o stream e limpa os intervalos */
function pararCamera() {
  if (streamAtivo) {
    streamAtivo.getTracks().forEach(t => t.stop());
    streamAtivo = null;
  }
  videoCamera.srcObject = null;
  clearInterval(intervaloCaptura);
  clearInterval(intervaloRecentes);
  intervaloCaptura = intervaloRecentes = null;

  btnIniciarCamera.disabled = false;
  btnPararCamera.disabled   = true;
  definirStatus("Câmera parada.", "neutro");
}

btnIniciarCamera.addEventListener("click", iniciarCamera);
btnPararCamera.addEventListener("click",   pararCamera);

// ── Tabela de Presenças Recentes ──────────────────────────────────────────────
const corpoTabelaRecentes = document.getElementById("corpoTabelaRecentes");

async function atualizarTabelaRecentes() {
  try {
    const resposta = await fetch(`${API_BASE}/presencas/hoje`);
    const dados    = await resposta.json();
    renderizarTabelaRecentes(dados.registros || []);
  } catch (_) {
    // falha silenciosa: tabela mantém o último estado
  }
}

function renderizarTabelaRecentes(registros) {
  if (!registros.length) {
    corpoTabelaRecentes.innerHTML =
      '<tr><td colspan="3" class="tabela__vazio">Sem registros hoje.</td></tr>';
    return;
  }

  corpoTabelaRecentes.innerHTML = registros
    .slice(0, 15)
    .map(r => `
      <tr>
        <td>${r.nome}</td>
        <td>${r.turma}</td>
        <td>${formatarDataHora(r.data_hora)}</td>
      </tr>`)
    .join("");
}

// ── Dashboard de Gestão ───────────────────────────────────────────────────────
const inputData             = document.getElementById("inputData");
const btnAtualizarDashboard = document.getElementById("btnAtualizarDashboard");
const totalPresencasEl      = document.getElementById("totalPresencas");
const horaMovimentaEl       = document.getElementById("horaMovimenta");
const canvasGrafico         = document.getElementById("graficoFluxo");

let instanciaGrafico = null;

// Define a data padrão do input como hoje
inputData.value = new Date().toISOString().split("T")[0];

async function carregarDashboard() {
  const dataEscolhida = inputData.value;
  const url = dataEscolhida
    ? `${API_BASE}/dashboard/fluxo?data=${dataEscolhida}`
    : `${API_BASE}/dashboard/fluxo`;

  try {
    const resposta = await fetch(url);
    const dados    = await resposta.json();
    renderizarGrafico(dados);
    calcularMetricas(dados);
  } catch (erro) {
    console.error("Falha ao carregar dashboard:", erro);
  }
}

function renderizarGrafico(dados) {
  const rotulos = Array.from({ length: 24 }, (_, h) => `${String(h).padStart(2, "0")}h`);
  const valores = Array(24).fill(0);

  dados.forEach(item => {
    if (item.hora >= 0 && item.hora < 24) {
      valores[item.hora] = item.total;
    }
  });

  if (instanciaGrafico) {
    instanciaGrafico.data.datasets[0].data = valores;
    instanciaGrafico.update();
    return;
  }

  instanciaGrafico = new Chart(canvasGrafico, {
    type: "bar",
    data: {
      labels: rotulos,
      datasets: [{
        label: "Presenças por Hora",
        data:  valores,
        backgroundColor: "rgba(45, 106, 159, 0.75)",
        borderColor:     "#2d6a9f",
        borderWidth:     1.5,
        borderRadius:    6,
      }],
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: ctx => ` ${ctx.parsed.y} aluno(s)`,
          },
        },
      },
      scales: {
        x: { grid: { display: false } },
        y: {
          beginAtZero: true,
          ticks: { stepSize: 1, precision: 0 },
          grid: { color: "#e0e7ef" },
        },
      },
    },
  });
}

function calcularMetricas(dados) {
  const total = dados.reduce((s, d) => s + d.total, 0);
  totalPresencasEl.textContent = total;

  if (dados.length) {
    const pico = dados.reduce((max, d) => d.total > max.total ? d : max, dados[0]);
    horaMovimentaEl.textContent = `${String(pico.hora).padStart(2, "0")}h`;
  } else {
    horaMovimentaEl.textContent = "—";
  }
}

btnAtualizarDashboard.addEventListener("click", carregarDashboard);

// ── Cadastro de Aluno ─────────────────────────────────────────────────────────
const videoCadastro     = document.getElementById("videoCadastro");
const canvasCadastro    = document.getElementById("canvasCadastro");
const btnCameraFoto     = document.getElementById("btnCameraFoto");
const btnCapturarFoto   = document.getElementById("btnCapturarFoto");
const btnDescartarFoto  = document.getElementById("btnDescartarFoto");
const previewFoto       = document.getElementById("previewFoto");
const imgPreview        = document.getElementById("imgPreview");
const formCadastro      = document.getElementById("formCadastro");
const btnCadastrar      = document.getElementById("btnCadastrar");
const statusCadastro    = document.getElementById("statusCadastro");
const cCanal            = document.getElementById("cCanal");
const grupoTelegramId   = document.getElementById("grupoTelegramId");

let streamCadastro  = null;
let fotoBase64      = null;

/** Exibe/oculta o campo de Telegram Chat ID conforme o canal selecionado */
cCanal.addEventListener("change", () => {
  grupoTelegramId.style.display = cCanal.value === "TELEGRAM" ? "block" : "none";
});

async function abrirCameraFoto() {
  try {
    streamCadastro = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
    videoCadastro.srcObject = streamCadastro;
    await videoCadastro.play();
    btnCameraFoto.disabled   = true;
    btnCapturarFoto.disabled = false;
  } catch (erro) {
    exibirStatusCadastro(`Câmera: ${erro.message}`, "erro");
  }
}

function capturarFotoCadastro() {
  const l = videoCadastro.videoWidth  || 640;
  const a = videoCadastro.videoHeight || 480;
  canvasCadastro.width  = l;
  canvasCadastro.height = a;
  canvasCadastro.getContext("2d").drawImage(videoCadastro, 0, 0, l, a);
  fotoBase64 = canvasCadastro.toDataURL("image/jpeg", 0.9);

  imgPreview.src        = fotoBase64;
  previewFoto.style.display = "block";
  btnCadastrar.disabled     = false;

  // Para a câmera após captura
  if (streamCadastro) {
    streamCadastro.getTracks().forEach(t => t.stop());
    streamCadastro = null;
  }
  videoCadastro.srcObject  = null;
  btnCameraFoto.disabled   = false;
  btnCapturarFoto.disabled = true;
}

function descartarFoto() {
  fotoBase64 = null;
  imgPreview.src            = "";
  previewFoto.style.display = "none";
  btnCadastrar.disabled     = true;
}

function exibirStatusCadastro(mensagem, tipo) {
  statusCadastro.style.display = "flex";
  statusCadastro.textContent   = mensagem;
  statusCadastro.style.background =
    tipo === "sucesso" ? "var(--verde-claro)"    :
    tipo === "erro"    ? "var(--vermelho-claro)" : "var(--branco)";
  statusCadastro.style.color =
    tipo === "sucesso" ? "var(--verde)"    :
    tipo === "erro"    ? "var(--vermelho)" : "var(--azul-escuro)";
}

async function submeterCadastro(evento) {
  evento.preventDefault();

  const nome       = document.getElementById("cNome").value.trim();
  const turma      = document.getElementById("cTurma").value.trim();
  const telefone   = document.getElementById("cTelefone").value.trim();
  const canal      = cCanal.value;
  const telegramId = document.getElementById("cTelegramId").value.trim() || null;

  if (!nome || !turma || !telefone) {
    exibirStatusCadastro("Preencha todos os campos obrigatórios.", "erro");
    return;
  }

  if (!fotoBase64) {
    exibirStatusCadastro("Capture a foto do aluno antes de cadastrar.", "erro");
    return;
  }

  btnCadastrar.disabled    = true;
  btnCadastrar.textContent = "⏳ Cadastrando...";

  try {
    const resposta = await fetch(`${API_BASE}/cadastrar`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        nome,
        turma,
        telefone_responsavel: telefone,
        imagem_base64:        fotoBase64,
        canal_preferencial:   canal,
        telegram_chat_id:     telegramId,
      }),
    });

    const dados = await resposta.json();

    if (resposta.ok) {
      exibirStatusCadastro(`✅ ${dados.mensagem} (ID: ${dados.aluno.id})`, "sucesso");
      formCadastro.reset();
      descartarFoto();
    } else {
      exibirStatusCadastro(`❌ ${dados.detail || "Erro no cadastro."}`, "erro");
    }

  } catch (erro) {
    exibirStatusCadastro(`Erro de conexão: ${erro.message}`, "erro");
  } finally {
    btnCadastrar.disabled    = false;
    btnCadastrar.textContent = "💾 Cadastrar Aluno";
  }
}

btnCameraFoto.addEventListener("click",  abrirCameraFoto);
btnCapturarFoto.addEventListener("click", capturarFotoCadastro);
btnDescartarFoto.addEventListener("click", descartarFoto);
formCadastro.addEventListener("submit",  submeterCadastro);
