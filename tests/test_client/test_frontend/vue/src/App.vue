<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import PcdViewer from './test/pcdViewer.vue';
import { BSON } from 'bson';
const ws_map = ref<{ [key: string]: WebSocket | null }>({ video_stream: null, pcdfile: null });
const viewer = ref<Viewer | null>(null)
const imgBlobUrl = ref<string | null>(null);

interface Viewer {
  createPointCloud: (points: number[][]) => void;
}

function initWebsocket(topic: string) {
  if (ws_map.value[topic]) return; 
  ws_map.value[topic] = new WebSocket("ws://localhost:8080/ws");

  ws_map.value[topic].onopen = () => {
    console.log("Websocket connected");
    subscribe(topic);

    // request first data
    requestData(topic);
  };

  ws_map.value[topic].onmessage = async (event) => {
    try {
      if (topic === "video_stream") {
        await create_video(event, topic);
      }

      if (topic === "pcdfile") {
        await create_pcd(event, topic);
      }
    }
    catch (e) {
      console.error("Error parsing message: " + e);
    }
  };

  ws_map.value[topic].onclose = () => {
    console.log("Websocket closed");
  };

  ws_map.value[topic].onerror = (error) => {
    console.error("Websocket error: " + error);
  };
}

function subscribe(topic : string) {
  if (ws_map.value[topic]) {
      ws_map.value[topic].send(JSON.stringify({
          type: "subscribe",
          topic: topic,
      }));
    }
}

function requestData(topic: string) {
  if (ws_map.value[topic]) {
    ws_map.value[topic].send(JSON.stringify({
        type: "request_data",
        topic: topic,
    }));
  }
}

async function create_video (event: { data: { arrayBuffer: () => any; }; },topic: string) {
  const arrayBuffer = await event.data.arrayBuffer();
      // console.log(`Received ${arrayBuffer.byteLength} bytes`);
      const uint8Array = new Uint8Array(arrayBuffer);
      // console.log(`Received ${uint8Array.length} bytes`);
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
      if (pixelSize == 32) {
        // RGBA
        const canvas = document.getElementById("videoCanvas") as HTMLCanvasElement;
        if (canvas) {
          const ctx = canvas.getContext("2d");
          if (ctx) {
            const imageData = new ImageData(new Uint8ClampedArray(imageDataArray), width, height);
            ctx.putImageData(imageData, 0, 0);
          } else {
            console.error("Error: Unable to get 2D context from canvas.");
          }
        } else {
          console.error("Error: Canvas element not found.");
        }
      }
      const blob = new Blob([imageDataArray]);
      imgBlobUrl.value = URL.createObjectURL(blob);
      console.log("Received Image");
      requestData(topic);
}

async function create_pcd (event: MessageEvent, topic: string) {
  const arrayBuffer = await event.data.arrayBuffer();
  const uint8Array = new Uint8Array(arrayBuffer);
  console.log("Received PCD file");
  const data = BSON.deserialize(uint8Array)

  if (Array.isArray(data.points) && data.points.length  !=  0 && viewer.value) {
    viewer.value.createPointCloud(data.points);
  }
  requestData(topic);
}

onMounted(() => {
  initWebsocket("video_stream");
  // initWebsocket("pcdfile");
});

onUnmounted(() => {
  if (ws_map.value) {
    for (const key in ws_map.value) {
      if (ws_map.value[key]) {
        ws_map.value[key]?.close();
      }
    }
  }
});
</script>

<template>
  <h1>test</h1>
  <canvas id="videoCanvas" width="1000" height="100"></canvas>
  <!-- <v-img :src="imgBlobUrl" v-if="imgBlobUrl" /> -->
  <h1>test2</h1>
  <PcdViewer ref="viewer"/>

</template>


