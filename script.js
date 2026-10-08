let port = null;
let writer = null;

const connectBtn = document.getElementById('connect-btn');
const statusText = document.getElementById('status-text');

if (!("serial" in navigator)) {
  alert("Váš prohlížeč nepodporuje rozhraní Web Serial API. Použijte nejnovější Google Chrome nebo Microsoft Edge.");
}

connectBtn.addEventListener('click', async () => {
  if (port) {
    await writer.releaseLock();
    await port.close();
    port = null;
    writer = null;
    updateUI(false);
    return;
  }

  try {
    port = await navigator.serial.requestPort();
    await port.open({ baudRate: 9600 });
    
    const textEncoder = new TextEncoderStream();
    const writableStreamClosed = textEncoder.readable.pipeTo(port.writable);
    writer = textEncoder.writable.getWriter();

    updateUI(true);
  } catch (err) {
    console.error("Chyba při připojování k sériovému portu: ", err);
    alert("Nepodařilo se připojit k zařízení.");
  }
});

function updateUI(isConnected) {
  if (isConnected) {
    statusText.innerText = "Připojeno";
    statusText.className = "status connected";
    connectBtn.innerText = "🔌 Odpojit Arduino";
  } else {
    statusText.innerText = "Odpojeno";
    statusText.className = "status disconnected";
    connectBtn.innerText = "🔌 Připojit Arduino";
  }

  const inputs = document.querySelectorAll('.control-panel input, .control-panel button');
  inputs.forEach(input => input.disabled = !isConnected);
}

async function sendServoCommand(servoId, angle) {
  if (writer) {
    const command = `${servoId} ${angle}\n`;
    await writer.write(command);
  }
}

for (let i = 1; i <= 5; i++) {
  const slider = document.getElementById(`servo${i}`);
  const valSpan = document.getElementById(`val-${i}`);

  if (slider) {
    slider.addEventListener('input', (e) => {
      valSpan.innerText = e.target.value;
      sendServoCommand(i, e.target.value);
    });
  }
}

const btnOpen = document.getElementById('btn-open');
const btnClose = document.getElementById('btn-close');

if (btnOpen) {
  btnOpen.addEventListener('click', () => {
    sendServoCommand(0, 100);
  });
}

if (btnClose) {
  btnClose.addEventListener('click', () => {
    sendServoCommand(0, 60);
  });
}

const copyBtn = document.getElementById('copy-code-btn');
if (copyBtn) {
  copyBtn.addEventListener('click', () => {
    const codeText = document.getElementById('arduino-code').innerText;
    navigator.clipboard.writeText(codeText);
    alert('Kód byl zkopírován do schránky!');
  });
}