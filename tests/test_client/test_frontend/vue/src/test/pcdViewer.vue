<script setup lang="ts">
import { Scene, PerspectiveCamera, WebGLRenderer,SphereGeometry,Group, BufferGeometry, BufferAttribute, MeshBasicMaterial, Points, Material, Box3, Vector3, ShaderMaterial, Color } from 'three'
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


// シェーダー
const vertexShader = `
  // attribute float size;
  attribute float intensity;
  uniform float minZ;
  uniform float maxZ;
  uniform int colorMode;
  uniform vec3 colorFix;
  uniform int colorMapMode;
  uniform float minIntensity;
  uniform float rangeIntensity;
  uniform float pointSize;
  uniform float opacity;
  varying float vOpacity;
  varying vec3 vColor;

  varying float vMode;

  const int TURBO = 0;
  const int INFERNO = 1;
  const int VIRIDIS = 2;
  const int PLASMA = 3;
  const int HSL = 4;

  const int COLORMODE_HEIGHT = 0;
  const int COLORMODE_INTENSITY = 1;
  const int COLORMODE_RGB = 2;
  const int COLORMODE_LABEL = 3;
  const int COLORMODE_FIXED = 4;
  const int COLORMODE_SCANDOWNLOAD = 5;
  const int COLORMODE_3D_DIFF = 6;
  const int COLORMODE_FULLMAP = 7;


  vec3 hsv2rgb(vec3 c) {
    vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
  }

  vec3 hsl2rgb( float c )
  {
    vec3 rgb = clamp( abs(mod(c*6.0+vec3(0.0,4.0,2.0),6.0)-3.0)-1.0, 0.0, 1.0 );
    return 0.5 + (rgb-0.5);
  }

  vec3 turbo_map(in float x) {
    const vec4 kRedVec4 = vec4(0.13572138, 4.61539260, -42.66032258, 132.13108234);
    const vec4 kGreenVec4 = vec4(0.09140261, 2.19418839, 4.84296658, -14.18503333);
    const vec4 kBlueVec4 = vec4(0.10667330, 12.64194608, -60.58204836, 110.36276771);
    const vec2 kRedVec2 = vec2(-152.94239396, 59.28637943);
    const vec2 kGreenVec2 = vec2(4.27729857, 2.82956604);
    const vec2 kBlueVec2 = vec2(-89.90310912, 27.34824973);

    x = clamp(x, 0.0, 1.0);
    vec4 v4 = vec4( 1.0, x, x * x, x * x * x);
    vec2 v2 = v4.zw * v4.z;
    return vec3(
      dot(v4, kRedVec4)   + dot(v2, kRedVec2),
      dot(v4, kGreenVec4) + dot(v2, kGreenVec2),
      dot(v4, kBlueVec4)  + dot(v2, kBlueVec2)
    );
  }
  vec3 inferno_map(float t) {
    const vec3 c0 = vec3(0.0002189403691192265, 0.001651004631001012, -0.01948089843709184);
    const vec3 c1 = vec3(0.1065134194856116, 0.5639564367884091, 3.932712388889277);
    const vec3 c2 = vec3(11.60249308247187, -3.972853965665698, -15.9423941062914);
    const vec3 c3 = vec3(-41.70399613139459, 17.43639888205313, 44.35414519872813);
    const vec3 c4 = vec3(77.162935699427, -33.40235894210092, -81.80730925738993);
    const vec3 c5 = vec3(-71.31942824499214, 32.62606426397723, 73.20951985803202);
    const vec3 c6 = vec3(25.13112622477341, -12.24266895238567, -23.07032500287172);
    return c0+t*(c1+t*(c2+t*(c3+t*(c4+t*(c5+t*c6)))));
  }
  vec3 viridis_map(float t) {
    const vec3 c0 = vec3(0.2777273272234177, 0.005407344544966578, 0.3340998053353061);
    const vec3 c1 = vec3(0.1050930431085774, 1.404613529898575, 1.384590162594685);
    const vec3 c2 = vec3(-0.3308618287255563, 0.214847559468213, 0.09509516302823659);
    const vec3 c3 = vec3(-4.634230498983486, -5.799100973351585, -19.33244095627987);
    const vec3 c4 = vec3(6.228269936347081, 14.17993336680509, 56.69055260068105);
    const vec3 c5 = vec3(4.776384997670288, -13.74514537774601, -65.35303263337234);
    const vec3 c6 = vec3(-5.435455855934631, 4.645852612178535, 26.3124352495832);
    return c0+t*(c1+t*(c2+t*(c3+t*(c4+t*(c5+t*c6)))));
  }
  vec3 plasma_map(float t) {
    const vec3 c0 = vec3(0.05873234392399702, 0.02333670892565664, 0.5433401826748754);
    const vec3 c1 = vec3(2.176514634195958, 0.2383834171260182, 0.7539604599784036);
    const vec3 c2 = vec3(-2.689460476458034, -7.455851135738909, 3.110799939717086);
    const vec3 c3 = vec3(6.130348345893603, 42.3461881477227, -28.51885465332158);
    const vec3 c4 = vec3(-11.10743619062271, -82.66631109428045, 60.13984767418263);
    const vec3 c5 = vec3(10.02306557647065, 71.41361770095349, -54.07218655560067);
    const vec3 c6 = vec3(-3.658713842777788, -22.93153465461149, 18.19190778539828);
    return c0+t*(c1+t*(c2+t*(c3+t*(c4+t*(c5+t*c6)))));
  }

  // Map Intensity to color
  void main() {
    float normalizedZ = (position.z - minZ) / (maxZ - minZ);
    float vMode = float(colorMode);
    if (colorMode == COLORMODE_INTENSITY) {
      float intensityNormalized = (intensity - minIntensity) / rangeIntensity;
      if (colorMapMode == TURBO)
        vColor = turbo_map(intensityNormalized);
      if (colorMapMode == INFERNO)
        vColor = inferno_map(intensityNormalized);
      if (colorMapMode == VIRIDIS)
        vColor = viridis_map(intensityNormalized);
      if (colorMapMode == PLASMA)
        vColor = plasma_map(intensityNormalized);
      if (colorMapMode == HSL)
        vColor = hsl2rgb(intensityNormalized);
    } else if (colorMode == COLORMODE_SCANDOWNLOAD) {
     // Red color for scan download
      vColor = vec3(1.0, 0.0, 0.0);
    } else if (colorMode == COLORMODE_3D_DIFF) {
     // White color for 3D diff
      vColor = vec3(1.0, 1.0, 1.0);
    } else if (colorMode == COLORMODE_FULLMAP) {
      vColor = vec3(1.0, 1.0, 1.0);
    }
    // vColor = hsv2rgb(vec3(normalizedZ, 1.0, 1.0));
    vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
    gl_PointSize = pointSize* (300.0 / -mvPosition.z);
    gl_Position = projectionMatrix * mvPosition;
  }
`

const fragmentShader = `
  varying vec3 vColor;
  uniform int colorMode;
  uniform float opacity;

  void main() {
    if (length(gl_PointCoord - vec2(0.5, 0.5)) > 0.475) discard;
    float alpha = 1.0;

    // 3d_diff, opacity is setting value
    if (colorMode == 6 || colorMode == 7) {
      alpha = opacity;
    }
    gl_FragColor = vec4(vColor, alpha);
  }
`

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

// create point cloud (for bson)
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
function createPointCloud(points:Float32Array, fields:string[], fieldData?: Float32Array) {
    const geometry = new BufferGeometry()

    geometry.setAttribute('position', new BufferAttribute(points, 3))
    let intensityRange = [0, 0]

    if (fields.includes('intensity')) {
      if (fieldData) {
        intensityRange[0] = Math.min(...fieldData)
      intensityRange[1] = Math.max(...fieldData)
      geometry.setAttribute('intensity', new BufferAttribute(fieldData, 1))
      }
    }

    const material = new ShaderMaterial({
    uniforms: {
      minZ: { value: -Infinity }, // for test
      maxZ: { value: Infinity }, // for test 
      colorMode: { value: 1 }, // 1: Intensity
      colorMapMode: { value: 0}, // 0: TURBO ,1: INFERNO, 2: VIRIDIS, 3: PLASMA, 4: HSL
      colorFix: { value: new Color(0xffffff) },
      pointSize: { value: 0.1 },
      opacity: { value: 0.9 },
      minIntensity: { value: intensityRange[0] },
      rangeIntensity: { value: intensityRange[1] - intensityRange[0] },
    },
    vertexShader: vertexShader,
    fragmentShader: fragmentShader,
    vertexColors: true,
    transparent: true,
  })
    // const material = new MeshBasicMaterial({ color: 0xff0000 })

    const pointCloud = new Points(geometry, material)
    pointsGroup.add(pointCloud);

    // add point
    pointNum.value += points.length; 

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