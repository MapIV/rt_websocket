<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import PcdViewer from './test/pcdViewer.vue';
import { BSON } from 'bson';
import { array } from 'three/tsl';
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

async function create_video (event: MessageEvent<any>,topic: string) {
  const arrayBuffer = event.data

  if (arrayBuffer.byteLength === 0) {
    console.log("Empty or invalid frame received, skipping update.");
    return;
  }
  const header = await arrayBuffer.slice(0,3).arrayBuffer()
  const formatBytes = new Uint8Array(header);
  const format = new TextDecoder("utf-8").decode(formatBytes); // "png" または "jpg"

  const mimeType = format === "png" ? "image/png" : "image/jpeg";
  const frameBytes = arrayBuffer.slice(3);

  const blob = new Blob([frameBytes], { type: mimeType });
  imgBlobUrl.value = URL.createObjectURL(blob);
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
  <!-- <canvas id="videoCanvas" width="1000" height="100"></canvas> -->
  <v-img :src="imgBlobUrl" v-if="imgBlobUrl" width="1000"/>
  <h1>test2</h1>
  <!-- <PcdViewer ref="viewer"/> -->

</template>


