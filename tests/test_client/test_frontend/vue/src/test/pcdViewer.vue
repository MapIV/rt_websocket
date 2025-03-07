<script setup lang="ts">
import { Scene, PerspectiveCamera, WebGLRenderer,SphereGeometry,Group, BufferGeometry, BufferAttribute, MeshBasicMaterial, Points, Material, Box3, Vector3 } from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

const renderArea = ref<HTMLElement | null>(null)
let scene = new Scene()
let camera = new PerspectiveCamera(90, window.innerWidth / window.innerHeight, 10, 5000)
const renderer = new WebGLRenderer({ antialias: true })
let controls: OrbitControls
const pointNum = ref(0)
let totalPointsController: any

// add group
let pointsGroup = new Group();
let pointCounter = 0;
const MAX_POINT_GROUPNUM = 2000;

// init settings
function init() {
    if (!renderArea.value) return

    // renderer
    renderer.setPixelRatio(window.devicePixelRatio)
    renderer.setSize(renderArea.value.clientWidth, renderArea.value.clientHeight)
    renderArea.value.appendChild(renderer.domElement)

    // init camera
    camera.position.z = 5 

    // add controls
    controls = new OrbitControls(camera, renderer.domElement)
    controls.enableDamping = true
    controls.dampingFactor = 0.25
    controls.enableZoom = true

    // initial point group
    pointNum.value = 0

    // add group
    scene.add(pointsGroup);

    animate()
}

function animate() {
    requestAnimationFrame(animate)
    controls.update()
    renderer.render(scene, camera)
    
}

// create point cloud
// function createPointCloud(points: number[][]) {
//     const geometry = new BufferGeometry()
//     const positions = new Float32Array(points.flatMap((p) => p.slice(0, 3)))
//     geometry.setAttribute('position', new BufferAttribute(positions, 3))

//     const material = new MeshBasicMaterial({ color: 0xff0000 })

//     const pointCloud = new Points(geometry, material)
//     pointsGroup.add(pointCloud);

//     // add point
//     pointNum.value += points.length; 

//     // Remove oldest points if exceeding maximum
//     if (pointsGroup.children.length > MAX_POINT_GROUPNUM ) {
//       pointNum.value -= pointsGroup.children[0].userData.pointCount;
//       (pointsGroup.children[0] as Points).geometry.deleteAttribute('position');
//       (pointsGroup.children[0] as Points).geometry.dispose();
//       ((pointsGroup.children[0] as Points).material as Material).dispose();
//       pointsGroup.remove(pointsGroup.children[0]);
//     }
//     console.log("pointNum: ", pointNum.value)
//     updateCamera()
// }
function createPointCloud(pointsWithIntensity:Float32Array) {
    const geometry = new BufferGeometry()
    // console.log("points: ", points)
    // Each point now has 4 values (x, y, z, intensity)
    // We need to extract just the x, y, z values for the position buffer
    const pointCount = pointsWithIntensity.length / 4;
    const positions = new Float32Array(pointCount * 3);
    const intensities = new Float32Array(pointCount);
    
    // Extract positions and intensities
    for (let i = 0; i < pointCount; i++) {
        positions[i * 3]     = pointsWithIntensity[i * 4];     // x
        positions[i * 3 + 1] = pointsWithIntensity[i * 4 + 1]; // y
        positions[i * 3 + 2] = pointsWithIntensity[i * 4 + 2]; // z
        intensities[i]       = pointsWithIntensity[i * 4 + 3]; // intensity
    }
    // const positions = new Float32Array(points.flatMap((p) => p.slice(0, 3)))
    geometry.setAttribute('position', new BufferAttribute(positions, 3))

    const material = new MeshBasicMaterial({ color: 0xff0000 })

    const pointCloud = new Points(geometry, material)
    pointsGroup.add(pointCloud);

    // add point
    pointNum.value += positions.length / 3; 

    // Remove oldest points if exceeding maximum
    if (pointsGroup.children.length > MAX_POINT_GROUPNUM ) {
      pointNum.value -= pointsGroup.children[0].userData.pointCount;
      (pointsGroup.children[0] as Points).geometry.deleteAttribute('position');
      (pointsGroup.children[0] as Points).geometry.dispose();
      ((pointsGroup.children[0] as Points).material as Material).dispose();
      pointsGroup.remove(pointsGroup.children[0]);
    }
    console.log("pointNum: ", pointNum.value)
    updateCamera()
}

// update camera

function updateCamera() {
  const bbox = new Box3()
  bbox.expandByObject(pointsGroup)

  const center = bbox.getCenter(new Vector3())
  const size = bbox.getSize(new Vector3())

  const maxDim = Math.max(size.x, size.y, size.z)
  const fov = camera.fov * (Math.PI / 180)
  let cameraZ = Math.abs(maxDim / 2 / Math.tan(fov / 2))
  cameraZ *= 1.5 // Zoom out a little so objects don't fill the screen

  camera.position.set(center.x, center.y, center.z + cameraZ)
  camera.near = cameraZ / 100
  camera.far = cameraZ * 100
  camera.updateProjectionMatrix()

  controls.target.copy(center)
  controls.update()
}

onMounted(() => {
    init()
})
onBeforeUnmount(() => {
    if (renderArea.value) {
        renderArea.value.removeChild(renderer.domElement)
    }
})

watch(pointNum, (newValue) => {
  if (totalPointsController) {
    totalPointsController.object['Total Points'] = newValue.toLocaleString()
    totalPointsController.updateDisplay()
  }
})

defineExpose({ 
    createPointCloud, 
    updateCamera 
    })
</script>

<template>
    <div ref="renderArea"></div>
  </template>
  
  <style scoped>
  div {
    width: 100%;
    height: 100vh;
  }
  </style>