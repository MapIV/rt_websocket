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
    requestData(topic,path); // for test
    requestData(topic,path); // for test
  };

  ws_map.value[topic].onmessage = async (event) => {
    try {
      if (topic === "video_stream") {
        await create_video(event, topic,path);
      }

      if (topic === "pcdfile") {
        await create_pcd(event, topic,path);
      }
      if (topic === "video_v9_stream") {
        await create_video_vp9(event, topic, path);
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

function testinitWebsocket() {
  const socket = new WebSocket("ws://localhost:8080/video");
  const imgTag = document.getElementById("video-frame")
  socket.onmessage = (event) => {
    imgTag.src = "data:image/jpeg;base64," + event.data;
  }
  socket.onclose = () => {
      console.log("WebSocket closed");
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
  
  if (arrayBuffer.byteLength < 3) {
    console.log("Empty or invalid frame received, skipping update.");
    return;
  }
  
  // Extract header (first 3 bytes)
  const headerBytes = new Uint8Array(arrayBuffer.slice(0, 3));
  const format = new TextDecoder("utf-8").decode(headerBytes);
  
  if (format === "end") {
    console.log("Received end signal. Stopping stream.");
    if (mediaSource.value?.readyState === "open") {
      // 1. `buffered` の最大値を取得
      const buffered = sourceBuffer.value?.buffered;
      console.log("buffered:", buffered);
      if (buffered && buffered.length > 0) {
        const lastBufferedTime = buffered.end(buffered.length - 1);
        mediaSource.value.duration = lastBufferedTime;  // 2. `duration` を設定
      }
      

      // 3. `endOfStream` を呼び出す
      // mediaSource.value.endOfStream();
    }
    return;
  }

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
  console.log("MediaSource readyState:", mediaSource.value?.readyState);
  // Add the H.264 chunk to the source buffer
  if (mediaSource.value?.readyState === "open" &&sourceBuffer.value && !sourceBuffer.value.updating) {
    try {
      if (sourceBuffer.value.buffered.length ==  0) {
        console.log("sourceBuffer.value.updating:", sourceBuffer.value.updating);
        console.log("Appending buffer:", vp9Data.byteLength);
        console.log("vp9Data:", vp9Data);
        sourceBuffer.value.appendBuffer(vp9Data);
      } else {
        // extract media segment 
        const ptr = extractInitSegment(0, vp9Data);4
        console.log("ptr:", ptr);
        if (typeof ptr === 'number') {
          const mediaSegment = extractMediaSegment(ptr, vp9Data);
          sourceBuffer.value.appendBuffer(mediaSegment);
        } else {
          console.error("Error: extractInitSegment did not return a number.");
        }

      }
      // console.log("sourceBuffer.value.updating:", sourceBuffer.value.updating);
      // console.log("Appending buffer:", vp9Data.byteLength);
      // console.log("vp9Data:", vp9Data);
      // sourceBuffer.value.appendBuffer(vp9Data);
      if (sourceBuffer.value) {
        console.log("buffered length:", sourceBuffer.value.buffered.length);
        console.log("buffered :", sourceBuffer.value.buffered);
        console.log("Buffered ranges:");
        for (let i = 0; i < sourceBuffer.value.buffered.length; i++) {
          console.log(`Range ${i}: ${sourceBuffer.value.buffered.start(i)} - ${sourceBuffer.value.buffered.end(i)}`);
        }
      }
      console.log("MediaSource readyState:", mediaSource.value?.readyState);
      // bufferQueue.value.push(vp9Data);
    } catch (e) {
      console.error("Error appending buffer:", e);
    }
  } else {
  console.warn("MediaSource is not open or sourceBuffer is busy.");
  bufferQueue.value.push(vp9Data);
  }
  
//   // Request next frame
//   requestData(topic, path);
}

async function create_text (event: MessageEvent, topic: string, path: string) {
  const json = JSON.parse(event.data);
  console.log("Received JSON data:", json);
  console.log("header:", json.header);
  console.log("data:", json.data);
  // requestData(topic, path);
}

function extractInitSegment(ptr: number, data: ArrayBuffer) {
  const webm = new Uint8Array(data);
  ptr = 0;

  const tagEBML = new Uint8Array([0x1a, 0x45, 0xdf, 0xa3]);
  const tagSegment = new Uint8Array([0x18, 0x53, 0x80, 0x67]);
  const tagCluster = new Uint8Array([0x1f, 0x43, 0xb6, 0x75]);

  function equal(a: Uint8Array, b: Uint8Array): boolean {
    return a.length === b.length && a.every((v, i) => v === b[i]);
  }

  function getElementSize(d: Uint8Array, p: number) {
    let l = 0;
    let n = d[p];
    let j;
    let t = 0;
    for (let i = 0; i < 8; i++) {
      if ((n >> (7 - i)) > 0) {
        j = i;
        break;
      }
    }
    for (let i = 0; i <= j!; i++) {
      let b = d[p + t];
      if (i == 0) b -= 1 << (7 - j!);
      l = l * 256 + b;
      t++;
    }
    return { length: l, offset: t };
  }

  if (!equal(tagEBML, webm.subarray(ptr, ptr + tagEBML.byteLength))) {
    console.error("WebM data error");
    return new ArrayBuffer(0);
  }
  ptr += tagEBML.byteLength;
  let r = getElementSize(webm, ptr);
  ptr += r.offset + r.length;

  if (!equal(tagSegment, webm.subarray(ptr, ptr + tagSegment.byteLength))) {
    console.error("WebM data error");
    return new ArrayBuffer(0);
  }
  ptr += tagSegment.byteLength;
  r = getElementSize(webm, ptr);
  ptr += r.offset;

  while (!equal(tagCluster, webm.subarray(ptr, ptr + tagCluster.byteLength))) {
    ptr++;
  }

  return ptr;
  
}

function extractMediaSegment(ptr: number,data: ArrayBuffer): ArrayBuffer {
  return data.slice(ptr);
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
  
  // Create MediaSource
  mediaSource.value = new MediaSource();
  videoElement.src = URL.createObjectURL(mediaSource.value);
  
  mediaSource.value.addEventListener('sourceopen', () => {
    try {
      // Create source buffer for VP9 video
      if (!sourceBuffer.value) {
        if (mediaSource.value) {
          console.log("Creating source buffer...");
          sourceBuffer.value = mediaSource.value.addSourceBuffer('video/webm; codecs="vp9"');
          // sourceBuffer.value.mode = 'sequence';
          sourceBuffer.value.mode = 'segments';
        }
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
    console.log("Buffer appended successfully. Playing video...");
    videoElement.play().catch((e) => console.error("Video play error:", e));
  });
  sourceBuffer.value?.addEventListener("updateend", () => {
    console.log("Buffer updated.");
  });
  console.log("MediaSource created:", mediaSource.value);
}

onMounted(() => {
  // initializeVideoPlayback();
  // initWebsocket("video_v9_stream","../src/sample_video/test_video1.mp4");
  // initWebsocket("text","test_path");
  // testinitWebsocket();
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
<h1>Live Stream</h1>
    <img src="http://localhost:8080/video" width="640" height="480" />

</template>


