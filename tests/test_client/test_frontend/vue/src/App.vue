<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import PcdViewer from './test/pcdViewer.vue';
import { BSON } from 'bson';
import { array, buffer } from 'three/tsl';
const ws_map = ref<{ [key: string]: WebSocket | null }>({ video_stream: null, pcdfile: null });
const viewer = ref<Viewer | null>(null)
const imgBlobUrl = ref<string | null>(null);
// const videoElement = ref<HTMLVideoElement | null>(null);
const mediaSource = ref<MediaSource | null>(null);
const sourceBuffer = ref<SourceBuffer | null>(null);
const bufferQueue = ref<ArrayBuffer[]>([]);

interface Viewer {
  createPointCloud: (points: Float32Array, fields:string[], fieldData?: Float32Array) => void;
}

function initWebsocket(topic: string,path: string) {
  if (ws_map.value[topic]) return; 
  ws_map.value[topic] = new WebSocket("ws://localhost:8080/ws");

  ws_map.value[topic].onopen = () => {
    console.log("Websocket connected");
    subscribe(topic,path);

    // request first data
    requestData(topic,path);
  };

  ws_map.value[topic].onmessage = async (event) => {
    try {
      if (topic === "video_stream") {
        await create_video(event, topic,path);
      }

      if (topic === "pcdfile") {
        await create_pcd(event, topic,path);
      }
      if (topic === "text") {
        await create_text(event, topic, path);
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

function subscribe(topic : string,path: string) {
  if (ws_map.value[topic]) {
      ws_map.value[topic].send(JSON.stringify({
          type: "subscribe",
          topic: topic,
          path: path,
      }));
    }
}

function requestData(topic: string,path: string) {
  if (ws_map.value[topic]) {
    ws_map.value[topic].send(JSON.stringify({
        type: "request_data",
        topic: topic,
        path: path,
    }));
  }
}

async function create_video (event: MessageEvent<any>,topic: string,path: string) {
  const arrayBuffer = event.data
  requestData(topic,path);
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
  // requestData(topic,path);
}

async function create_pcd (event: MessageEvent, topic: string,path: string) {
  console.log("Received PCD file time: ", new Date().getTime());
  const arrayBuffer = await event.data.arrayBuffer();

  // read header length
  const headerLengthbyte = arrayBuffer.slice(0,4);
  const headerLengthInt = new DataView(headerLengthbyte).getInt32(0, true);
  console.log("headerLength : ", headerLengthInt);

  // read header
  const headerbytes = arrayBuffer.slice(4,4+headerLengthInt);
  const headerText = new TextDecoder("utf-8").decode(headerbytes);
  const header = JSON.parse(headerText);
  console.log("header : ", header);

  // Get points and field data lengths from header
  const pointsLength = header.points_length;
  const fieldLength = header.field_length;
  const fields = header.fields;

  // Extract points data
  const pointsStart = 4 + headerLengthInt;
  const pointsBuffer = arrayBuffer.slice(pointsStart, pointsStart + pointsLength);
  const positions = new Float32Array(pointsBuffer);
  
  // Extract field data if available
  let fieldData = new Float32Array(0);
  if (fieldLength > 0) {
    const fieldStart = pointsStart + pointsLength;
    const fieldBuffer = arrayBuffer.slice(fieldStart, fieldStart + fieldLength);
    fieldData = new Float32Array(fieldBuffer);
  }
  console.log("fieldData.length : ", fieldData.length);
  console.log("points.length : ", positions.length);
  console.log("fields : ", fields );

  if (viewer.value) {
    if (fieldData.length > 0) {
      viewer.value.createPointCloud(positions, fields,fieldData,);
    } else {
    viewer.value.createPointCloud(positions, fields);
    }
  }
  console.log("finish create pcd time : ", new Date().getTime());
  requestData(topic,path);
}

async function create_text (event: MessageEvent, topic: string, path: string) {
  const json = JSON.parse(event.data);
  console.log("Received JSON data:", json);
  console.log("header:", json.header);
  console.log("data:", json.data);
  requestData(topic, path);
}


onMounted(() => {
  // initWebsocket("video_stream","../src/sample_video/test_video1.mp4"); // docker container内のパス
  initWebsocket("pcdfile","../src/sample_pcdfile/map-18400_-93500_converted_converted.pcd");// docker container内のパス
  // initWebsocket("text","test_path");// docker container内のパス
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
  <v-img :src="imgBlobUrl" v-if="imgBlobUrl" width="1000"/>
  <h1>test2</h1>
  <PcdViewer ref="viewer"/>
  <h1>H.264 Video Stream</h1>
  <div >
    <video id="videoContainer"></video>
  </div>

  <h1>Local WebM Video</h1>
<div id="videoContainer2">
  <video width="640" height="480" controls autoplay>
    <source src="/src/assets/test_video1.webm" type="video/webm">
    Your browser does not support the video tag.
  </video>
</div>
<h1>rtc</h1>
    <video controls autoplay>
    <source src="http://localhost:8080/video?video_path=../src/sample_video/test_video1.mp4" type="video/mp4">
    Your browser does not support the video tag.
</video>
</template>


