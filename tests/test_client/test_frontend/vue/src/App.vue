<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
const ws = ref<WebSocket | null>(null)

function initWebsocket() {
  ws.value = new WebSocket("ws://localhost:8080/ws");

  ws.value.onopen = () => {
    console.log("Websocket connected");
    subscribe();

    // request first data
    requestData();
  };

  ws.value.onmessage = async (event) => {
    try {
      const arrayBuffer = await event.data.arrayBuffer();
      console.log(`Received ${arrayBuffer.byteLength} bytes`);
      const uint8Array = new Uint8Array(arrayBuffer);
      console.log(`Received ${uint8Array.length} bytes`);
      // header(width, height, pixel_size）
      const headerArray = new Uint32Array(arrayBuffer.slice(0, 12)); // 3 * 4 bytes
      const width = headerArray[0];
      const height = headerArray[1];
      const pixelSize = headerArray[2];
      console.log(`Received Frame - Width: ${width}, Height: ${height}, PixelSize: ${pixelSize}`);

      // image data
      const imageDataArray  = uint8Array.slice(12);
      if (pixelSize === 24) {
            // RGB → RGBA に変換
            const rgbaArray = new Uint8ClampedArray(width * height * 4);
            for (let i = 0, j = 0; i < imageDataArray.length; i += 3, j += 4) {
                rgbaArray[j] = imageDataArray[i];     // R
                rgbaArray[j + 1] = imageDataArray[i + 1]; // G
                rgbaArray[j + 2] = imageDataArray[i + 2]; // B
                rgbaArray[j + 3] = 255; // A (不透明)
            }

            // Canvas に描画
            const canvas = document.getElementById("videoCanvas") as HTMLCanvasElement;
            if (canvas) {
                const ctx = canvas.getContext("2d");
                if (ctx) {
                  const imageData = new ImageData(rgbaArray, width, height);
                  ctx.putImageData(imageData, 0, 0);
                } else {
                  console.error("Error: Unable to get 2D context from canvas.");
                }
            } else {
              console.error("Error: Canvas element not found.");
            }
        }
      requestData();
    }
    catch (e) {
      console.error("Error parsing message: " + e);
    }
  };

  ws.value.onclose = () => {
    console.log("Websocket closed");
  };

  ws.value.onerror = (error) => {
    console.error("Websocket error: " + error);
  };
}

function subscribe() {
  if (ws.value) {
      ws.value.send(JSON.stringify({
          type: "subscribe",
          topic: "video_stream"
      }));
    }
}

function requestData() {
  if (ws.value) {
    ws.value.send(JSON.stringify({
        type: "request_data",
        topic: "video_stream"
    }));
  }
}

onMounted(() => {
  initWebsocket();
});
</script>

<template>
  <h1>test</h1>
  <canvas id="videoCanvas" width="1280" height="1000"></canvas>
</template>


