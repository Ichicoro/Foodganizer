import * as THREE from "https://cdn.skypack.dev/three@v0.133.1"
import { GLTFLoader } from "https://cdn.skypack.dev/three@v0.133.1/examples/jsm/loaders/GLTFLoader"
import { OrbitControls } from "https://cdn.skypack.dev/three@v0.133.1/examples/jsm/controls/OrbitControls"

let config = {
    ambientColor: 0x775555, // 0xedcdab
    lightColor: 0xffffff,
    primarySpotLightColor: 0x3000ff,
    secondarySpotLightColor: 0xff0030,
    rectLightColor: 0x0077ff,
}

// config = {
//     backgroundColor: 0x1b1b1b,
//     ambientColor: 0x2900af,
//     spotLightColor: 0x3000ff,
//     rectLightColor: 0x0077ff,
//     meshMaterial: {
//         color: 0xff00ff,
//         metalness: 0.58,
//         roughness: 0.18
//     }
// }


function showFridge() {
    const fridgeEl = document.querySelector("#fridge")
    const scene = new THREE.Scene()
    // const camera = new THREE.PerspectiveCamera(60, fridgeEl.clientWidth / fridgeEl.clientHeight, 0.1, 1000)
    const camera = new THREE.OrthographicCamera(fridgeEl.clientWidth / -175, fridgeEl.clientWidth / 175, fridgeEl.clientHeight / 175, fridgeEl.clientHeight / -175, 0.1, 1000)

    let fridgeNode
    const loader = new GLTFLoader()
    loader.load(
        "/static/fridge/frigo.glb",
        gltf => {
            gltf.scene.traverse(child => {
                if (child.isMesh) {
                    child.geometry.center()     // center node
                    child.castShadow = true
                    child.receiveShadow = true
                    // child.material.metalness = config.meshMaterial.metalness
                    // child.material.color = [0.5,0.5,0,0]
                    // child.material.roughness = config.meshMaterial.roughnes`s
                    // fridgeNode = child
                    child.material.roughness = 1
                }
            })
            // gltf.scene.scale.set(.075,.075,.075)      // scale node
            gltf.scene.scale.set(1,0.8,1)

            fridgeNode = gltf.scene
            scene.add(gltf.scene)
        },
        xhr => console.log((xhr.loaded / xhr.total * 100).toFixed(2) + '% loaded'),
        error => {} // There are no errors in Ba Sing Se
    )

    // Create renderer and add it to the DOM
    const renderer = new THREE.WebGLRenderer({
        alpha: true,
        antialias: true
    })
    fridgeEl.appendChild(renderer.domElement)

    // Set everything to transparent
    scene.background = null
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.setClearColor(0x000000, 0); //default
    renderer.setSize(fridgeEl.clientWidth, fridgeEl.clientHeight)

    // Setup
    const orbitControls = new OrbitControls(camera, renderer.domElement)
    orbitControls.autoRotate = true
    orbitControls.autoRotateSpeed = 5.0
    orbitControls.enableZoom = false
    orbitControls.enablePan = false
    orbitControls.enableDamping = true
    orbitControls.minPolarAngle = Math.PI/2*0.75
    orbitControls.maxPolarAngle = Math.PI/2*0.75

    // Add point light
    const light = new THREE.PointLight(config.primarySpotLightColor, 1, 100)
    light.position.set(50, 50, -50)
    scene.add(light)

    if (config.secondarySpotLightColor) {
        const light2 = new THREE.PointLight(config.secondarySpotLightColor, 1, 100)
        light2.position.set(-50, 50, 50)
        scene.add(light2)
    }

    // Add ambient light
    if (config.ambientColor) {
        const ambientLight = new THREE.AmbientLight(config.ambientColor) // soft white light
        scene.add(ambientLight)
    }

    // Add rect light
    if (config.rectLightColor) {
        const rectLight = new THREE.RectAreaLight(config.rectLightColor, 1, 2000, 2000);
        rectLight.position.set(5, 10, 50);
        rectLight.lookAt(0, 0, 0);
        scene.add(rectLight);
    }

    camera.position.z = 4

    function animate() {
        requestAnimationFrame(animate)

        orbitControls.update()
        // light.rotation.y += 0.01

        renderer.render(scene, camera)
    }
    animate()
}

$$onReady(() => showFridge())