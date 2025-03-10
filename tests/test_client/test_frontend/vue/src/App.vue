<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import PcdViewer from './test/pcdViewer.vue';
import { BSON } from 'bson';
import { array } from 'three/tsl';
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
      if (topic === "video_h264_stream") {
        await create_video_vp9(event, topic, path);
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
  requestData(topic,path);
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

async function create_video_vp9 (event: MessageEvent, topic: string, path: string) {
  const arrayBuffer = await event.data.arrayBuffer();
  
  if (arrayBuffer.byteLength <= 3) {
    console.log("Empty or invalid frame received, skipping update.");
    return;
  }
  
  // Extract header (first 3 bytes)
  const headerBytes = new Uint8Array(arrayBuffer.slice(0, 3));
  const format = new TextDecoder("utf-8").decode(headerBytes);
  
  if (format !== "vp9") {
    console.error("Invalid format received:", format);
    return;
  }
  
  // Get the encoded vp9Data data
  const vp9Data = arrayBuffer.slice(3);
  console.log("Received vp9Data frame:", vp9Data.byteLength);
  
  // Create MSE (Media Source Extensions) components if not already created
  if (!mediaSource.value) {
    initializeVideoPlayback();
  }
  
  // Add the H.264 chunk to the source buffer
  if (mediaSource.value?.readyState === "open" &&sourceBuffer.value && !sourceBuffer.value.updating) {
    try {
      console.log("sourceBuffer.value.updating:", sourceBuffer.value.updating);
      console.log("Appending buffer:", vp9Data.byteLength);
      sourceBuffer.value.appendBuffer(vp9Data);
      console.log("MediaSource readyState:", mediaSource.value?.readyState);
      // bufferQueue.value.push(vp9Data);
    } catch (e) {
      console.error("Error appending buffer:", e);
    }
  } else {
  console.warn("MediaSource is not open or sourceBuffer is busy.");
  }
  // setTimeout(() => {
  //   requestData(topic, path);
  // }, 1000);
  // Request next frame
  requestData(topic, path);
}

function initializeVideoPlayback() {
  // Create a video element if using programmatically
  // Or reference the existing video element from the template
  //videoElement.value = document.createElement('video');
  const videoElement = document.getElementById('videoContainer') as HTMLVideoElement;; 
  if (!videoElement) {
    console.error("Video element not found.");
    return;
  }
  videoElement.width = 640;
  videoElement.height = 480;
  videoElement.controls = true;
  videoElement.autoplay = true;
  
  // Append to DOM if creating programmatically
  // const container = document.getElementById('videoContainer');
  // if (container) {
  //   container.appendChild(videoElement.value);
  // }
  
  // Create MediaSource
  mediaSource.value = new MediaSource();
  videoElement.src = URL.createObjectURL(mediaSource.value);
  
  mediaSource.value.addEventListener('sourceopen', () => {
    try {
      // Create source buffer for VP9 video
      if (!sourceBuffer.value) {
        sourceBuffer.value = mediaSource.value?.addSourceBuffer('video/webm; codecs="vp9"');
        // sourceBuffer.value.mode = 'segments';
      sourceBuffer.value.mode = 'sequence';
      console.log("Source buffer created:", sourceBuffer.value);
      }
    } catch (e) {
      console.error('Error creating source buffer:', e);
    }
  });
  mediaSource.value.addEventListener('sourceended', (e) =>  { console.log('sourceended: ' + mediaSource.value?.readyState); });
  mediaSource.value.addEventListener('sourceclose', (e) => { console.log('sourceclose: ' + mediaSource.value?.readyState); });
  mediaSource.value.addEventListener('error', (e) =>  { console.log('error: ' + mediaSource.value?.readyState); });
  mediaSource.value.addEventListener('sourceopen', (e) =>  { console.log('sourceopen: ' + mediaSource.value?.readyState); });
  sourceBuffer.value?.addEventListener("onerror", (e) => {
    console.error("Source buffer error:", e);
  });
  sourceBuffer.value?.addEventListener("onupdateend", () => {
    // const buffer = bufferQueue.value.shift();
    // console.log("sourceBuffer.value.updating:", sourceBuffer.value?.updating);
    // sourceBuffer.value?.appendBuffer(buffer?buffer:new ArrayBuffer(0));
    console.log("Buffer appended successfully. Playing video...");
    videoElement.play().catch((e) => console.error("Video play error:", e));
  });
}

onMounted(() => {
  // initWebsocket("video_stream","../src/sample_video/test_video1.mp4"); // docker container内のパス
  // initWebsocket("pcdfile","../src/sample_pcdfile/map-18400_-93500_converted_converted.pcd"); // docker container内のパス
  initWebsocket("video_h264_stream","../src/sample_video/test_video1.mp4");
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
    <video id="videoContainer" controls autoplay></video>
  </div>

  <h1>Local WebM Video</h1>
<div id="videoContainer2">
  <video width="640" height="480" controls autoplay>
    <source src="/src/assets/test_video1.webm" type="video/webm">
    Your browser does not support the video tag.
  </video>
</div>

</template>


