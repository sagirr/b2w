

bl_info = {
    "name" : "B2W",
    "author" : "ş@gir",
    "description" : "Blender TO WEB B2W",
    "blender" : (3, 5, 0),
    "version" : (0, 0, 11),
    "location" : "View3D",
    "warning" : "",
    "category" : "3D View"
}

import os
import bpy
import shutil
import math
from string import Template
import http.server
import urllib.request
import socketserver
import threading
import json
import random
import string

PORT = 8001

# Constants
PATH_INDEX = "index.html"
PATH_ENABLED = "enabled.html"
PATH_INDEX_RENDERED = "render.html"
PATH_INDEX_AR = "ar.html"
PATH_ASSETS = "assets/"
PATH_RESOURCES = "resources/"
PATH_MEDIA = "media/"
PATH_ENABLED_DIR="enabled/"
PATH_ENABLED_JS = "enabled/js/"
PATH_ENABLED_LIB = "enabled/lib/"
PATH_ENABLED_LIB_MOZ = "enabled/lib/ammo/moz/"
PATH_BUILD = "r147/build/"
PATH_LIGHTMAPS = "lightmaps/"
PATH_JAVASCRIPT_LOADERS = "r147/r147/jsm/loaders/"
PATH_JAVASCRIPT_EXPORTERS = "r147/r147/jsm/exporters/"
PATH_JAVASCRIPT_CONTROLS = "r147/r147/jsm/controls/"
PATH_JAVASCRIPT_LIBS = "r147/r147/jsm/libs/"
PATH_ENV= "env/"
threejs_ANIMATION = "threejs_ANIMATION"
threejs_IMAGES = "threejs_IMAGES"

assets = []
entities = []
lights = []
blender_lights = []
final_lights = ""

# Need to subclass SimpleHTTPRequestHandler so we can serve cache-busting headers
class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_my_headers()
        http.server.SimpleHTTPRequestHandler.end_headers(self)

    def send_my_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")

class Server(threading.Thread):
    instance = None
    folder = ""
    should_stop = False
        
    def set_folder(self, folder):
        self.folder = folder
        
    def run(self):
        Handler = MyHTTPRequestHandler
        socketserver.TCPServer.allow_reuse_address = True
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            os.chdir(self.folder)
            while True:
                if self.should_stop:
                    httpd.server_close()
                    break
                httpd.handle_request()

    def stop(self):
        self.should_stop = True
        # Consume the last handle_request call that's still pending
        with urllib.request.urlopen(f'http://localhost:{PORT}/') as response:
            html = response.read()


# Index html threejs template
def default_template():
    if not bpy.data.texts.get('index.html'):
        tpl = bpy.data.texts.new('index.html')
        tpl.from_string('''

<!DOCTYPE html>
<html lang="en">
	<head>
		<title>blender to threejs -</title>
		<meta charset="utf-8">
		<meta name="viewport" content="width=device-width, user-scalable=no, minimum-scale=1.0, maximum-scale=1.0">
		<link type="text/css" rel="stylesheet" href="main.css">
        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.4.1/css/bootstrap.min.css">
  <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.7.1/jquery.min.js"></script>
        	<style>
  .button-container {
    position: absolute;
    z-index: 999;
    left: 0;
    top: 10px;
  }

  .button {
    display: inline-block;
    padding: 5px 16px;
    font-size: 16px;
    text-align: center;
    text-decoration: none;
    background-color: #4CAF50; /* Green background */
    color: white; /* White text color */
    border: 1px solid #4CAF50; /* Green border */
    border-radius: 5px; /* Rounded corners */
    cursor: pointer;
  }

  .button:hover {
    background-color: #45a049; /* Darker green on hover */
  }
   .btnred{
    background-color: red;
  }
</style>
	</head>

	<body>
	<div style="position:absolute;z-index:999;left:0;top:10px">
<a href="enabled.html" class="button">Fps</a>
<a href="http://localhost:8001/" class="button btnred">Viewer</a>
<a href="#render.html" class="button" id="exporter">Render</a>
 <a href="ar.html" class="btn btn-success button" >AR</a>
</div>	
<div class="yaz" style="display:none;position:absolute;top:0;left:0;z-index:9999; height:100%;width:100%;">
			
  <iframe class="yz" src=""   style="width:100%;height:100%; " frameborder="0">
	</iframe>
	
					   
  </div> 
  
  	<button class="btn btn-info cursor ifrbtn" id="yazbuton" style="position:absolute;z-index:999999;left:0;bottom:0;background-color:red;height:33px;width:100%;display:none"  >X</button>
		<script type="importmap">
			{
				"imports": {
				"three": "./r147/build/three.module.js",
					"three/addons/": "./r147/r147/jsm/"
				}
			}
		</script>


		<script type="module">

			import * as THREE from 'three';

			import { GUI } from 'three/addons/libs/lil-gui.module.min.js';
			import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
			import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
            import { GLTFExporter } from 'three/addons/exporters/GLTFExporter.js';
			import { RGBELoader } from 'three/addons/loaders/RGBELoader.js';

			let mesh, renderer, scene, camera, controls,lightData,models;
			let  guiExposure = null;
            let gui = new GUI();
            let lightHelpers = [];
			const params = {
				exposure: 1.0,
				toneMapping: 'ACESFilmic',
				blurriness: 0.3,
				intensity: 1.0,
			};

			const toneMappingOptions = {
				None: THREE.NoToneMapping,
				Linear: THREE.LinearToneMapping,
				Reinhard: THREE.ReinhardToneMapping,
				Cineon: THREE.CineonToneMapping,
				ACESFilmic: THREE.ACESFilmicToneMapping,
				Custom: THREE.CustomToneMapping
			};

			init().catch( function ( err ) {

				console.error( err );

			} );


        const yazButton = document.getElementById('yazbuton');
        const yazDiv = document.querySelector('.yaz');

        yazButton.addEventListener('click', function() {
          yazDiv.style.display = 'none';
          yazButton.style.display = 'none';
        });

			async function init() {

				renderer = new THREE.WebGLRenderer( { antialias: true } );
				renderer.setPixelRatio( window.devicePixelRatio );
				renderer.setSize( window.innerWidth, window.innerHeight );
				document.body.appendChild( renderer.domElement );

				renderer.toneMapping = toneMappingOptions[ params.toneMapping ];
				renderer.toneMappingExposure = params.exposure;
                renderer.shadowMap.enabled = true;
                renderer.shadowMap.type = THREE.PCFSoftShadowMap;
				// Set CustomToneMapping to Uncharted2
				// source: http://filmicworlds.com/blog/filmic-tonemapping-operators/

				THREE.ShaderChunk.tonemapping_pars_fragment = THREE.ShaderChunk.tonemapping_pars_fragment.replace(

					'vec3 CustomToneMapping( vec3 color ) { return color; }',

					`#define Uncharted2Helper( x ) max( ( ( x * ( 0.15 * x + 0.10 * 0.50 ) + 0.20 * 0.02 ) / ( x * ( 0.15 * x + 0.50 ) + 0.20 * 0.30 ) ) - 0.02 / 0.30, vec3( 0.0 ) )

					float toneMappingWhitePoint = 1.0;

					vec3 CustomToneMapping( vec3 color ) {
						color *= toneMappingExposure;
						return saturate( Uncharted2Helper( color ) / Uncharted2Helper( vec3( toneMappingWhitePoint ) ) );

					}`

				);

				scene = new THREE.Scene();
				scene.backgroundBlurriness = params.blurriness;

				camera = new THREE.PerspectiveCamera(  50, window.innerWidth / window.innerHeight, 0.01, 1000 );
        camera.position.set( 0,23,10 );
        camera.minDistance = 0;
		camera.maxDistance = 1000;
		camera.enableDamping = true;
		

				controls = new OrbitControls( camera, renderer.domElement );
				controls.addEventListener( 'change', render ); // use if there is no animation loop
				controls.enableZoom = true;
				controls.enablePan = true;
				controls.target.set( 0, 0, - 0.2 );
				controls.update();


                lightData = [
                             ${lights} 
                            ];

                  models = [ ${entity}];

             let model;
					const loader = new GLTFLoader();

					function loadModel(modelInfo, modelIndex) {
						loader.load(modelInfo.path, function (gltf) {
							model = gltf.scene;
							model.position.set(modelInfo.position[0],modelInfo.position[1],modelInfo.position[2]);
                            
                            
							const modelFolder = gui.addFolder('Model '+modelIndex);

							scene.add(model);

							model.traverse((child) => {
								if (child.isMesh) {
									child.castShadow = true;
									child.receiveShadow = true;

									const component = { [ child.name]: 1.0 };
									modelFolder.add(component, child.name, 0, 1).onChange((value) => {
										child.material.opacity = value;
										child.material.transparent=true;
										render();
									});
									
									const colorParams = { [child.name + ' Color']: '#ffffff' }; // Varsayılan renk değeri
									modelFolder.addColor(colorParams, child.name + ' Color').onChange((value) => {
										child.material.color.set(value);
										render();
									});
									
									const roughnessParams = { [child.name + ' Roughness']: 0.5 }; // Varsayılan roughness değeri
									modelFolder.add(roughnessParams, child.name + ' Roughness', 0, 2).onChange((value) => {
										child.material.roughness = value;
										render();
									});
									
									const metalnessParams = { [child.name + ' Metalness']: 0.5 }; // Varsayılan roughness değeri
									modelFolder.add(metalnessParams, child.name + ' Metalness', 0, 2).onChange((value) => {
										child.material.metalness = value;
										render();
									});
									
									modelFolder.close();
									
								}
							});

							render();
						});
					}

					// Tüm modelleri yükle
					models.forEach(loadModel);

                     lightData.forEach(lightInfo => {
					  const lightType = lightInfo.light.type;
					  let lightd;

					  if (lightType === 'Directional') {
						lightd = new THREE.DirectionalLight(lightInfo.light.color, lightInfo.light.intensity);
						lightd.castShadow = lightInfo.light.castShadow;
					  } else if (lightType === 'Point') {
						lightd = new THREE.PointLight(lightInfo.light.color, lightInfo.light.intensity);
						lightd.castShadow = lightInfo.light.castShadow;
						// Diğer PointLight özelliklerini burada ayarlayın
					  } else if (lightType === 'Spot') {
						lightd = new THREE.SpotLight(lightInfo.light.color, lightInfo.light.intensity);
						lightd.castShadow = lightInfo.light.castShadow;
						// Diğer SpotLight özelliklerini burada ayarlayın
					  }

					  // Diğer ışık türleri eklenirse bu else if blokları genişletilebilir

					  lightd.position.set(lightInfo.position[0], lightInfo.position[1], lightInfo.position[2]);

					  // Işık görselleştirmesi için LightHelper oluştur
					  const lightHelper = new THREE[lightType + 'LightHelper'](lightd);

					  // Helper'ın pozisyonunu ayarla
					  lightHelper.position.set(lightInfo.position[0], lightInfo.position[1], lightInfo.position[2]);

					  // Helper'ı sahneye ekle, ancak başlangıçta gizle
					  lightHelper.visible = false;
					  scene.add(lightHelper);
					  lightHelpers.push(lightHelper);

					  // Gölge özelliklerini ayarla
					  if (lightd.castShadow) {
						lightd.shadow.bias = lightInfo.light.shadowBias;
						lightd.shadow.camera.far = lightInfo.light.shadowCameraFar;
						lightd.shadow.camera.bottom = lightInfo.light.shadowCameraBottom;
						lightd.shadow.camera.fov = lightInfo.light.shadowCameraFov;
						lightd.shadow.camera.near = lightInfo.light.shadowCameraNear;
						lightd.shadow.camera.top = lightInfo.light.shadowCameraTop;
						lightd.shadow.camera.right = lightInfo.light.shadowCameraRight;
						lightd.shadow.camera.left = lightInfo.light.shadowCameraLeft;
						lightd.shadow.radius = lightInfo.light.shadowRadius;
						lightd.shadow.bias = -0.0005;
					  }

					  scene.add(lightd);

					  const folder = gui.addFolder(lightType+'Light '+lightData.indexOf(lightInfo) + 1);


					  // Add controls for color
					  const colorControl = folder.addColor(lightInfo.light, 'color');
					  colorControl.onChange(() => {
						lightd.color.set(lightInfo.light.color);
						render();
					  });

					  // Add control for intensity
					  const intensityControl = folder.add(lightInfo.light, 'intensity', 0, 2);
					  intensityControl.onChange(() => {
						lightd.intensity = lightInfo.light.intensity;
						render();
					  });

					  // Add control for helper visibility
					  folder.add({ ['Show Light Helper']: false }, 'Show Light Helper').onChange((value) => {
						lightHelper.visible = value;
						render();
					  });

					  folder.close();
					});

				const rgbeLoader = new RGBELoader()
					.setPath( 'env/' );

				
				// RGBe ve modellerin yüklenmesini bekleyin
				const [texture] = await Promise.all([
					rgbeLoader.loadAsync('venice_sunset_1k.hdr')
				]);

				// environment
				texture.mapping = THREE.EquirectangularReflectionMapping;
				scene.background = texture;
				scene.environment = texture;


            



				render();

				window.addEventListener( 'resize', onWindowResize );

				const toneMappingFolder = gui.addFolder( 'tone mapping' );

				toneMappingFolder.add( params, 'toneMapping', Object.keys( toneMappingOptions ) )

					.onChange( function () {

						updateGUI( toneMappingFolder );

						renderer.toneMapping = toneMappingOptions[ params.toneMapping ];
						render();

					} );


				const backgroundFolder = gui.addFolder( 'background' );

				backgroundFolder.add( params, 'blurriness', 0, 1 )

					.onChange( function ( value ) {

						scene.backgroundBlurriness = value;
						render();

					} );

				backgroundFolder.add( params, 'intensity', 0, 1 )

					.onChange( function ( value ) {

						scene.backgroundIntensity = value;
						render();

					} );

				updateGUI( toneMappingFolder );

				gui.open();

			}

			function updateGUI( folder ) {

				if ( guiExposure !== null ) {

					guiExposure.destroy();
					guiExposure = null;

				}

				if ( params.toneMapping !== 'None' ) {

					guiExposure = folder.add( params, 'exposure', 0, 2 )

						.onChange( function () {

							renderer.toneMappingExposure = params.exposure;
							render();

						} );

				}

			}
            
 const exportButton = document.getElementById('exporter');
			   
				exportButton.addEventListener('click', () => {
				  const exporter = new GLTFExporter();
				  exporter.parse(scene, (gltf) => {
					const blob = new Blob([JSON.stringify(gltf)], { type: 'application/json' });
					const url = URL.createObjectURL(blob);

					 document.querySelector('.yz').setAttribute('src', 'render.html?hdr=env/venice_sunset_1k.hdr&blob=' + url);

                        document.querySelector('.yaz').style.display = 'block';
                        document.querySelector('#yazbuton').style.display = 'block';

				  });
				});

			function onWindowResize() {

				camera.aspect = window.innerWidth / window.innerHeight;

				camera.updateProjectionMatrix();

				renderer.setSize( window.innerWidth, window.innerHeight );

				render();

			}

			function render() {

				renderer.render( scene, camera );

			}

		</script>

	</body>
</html>


''')









def default_template_enabled():
    if not bpy.data.texts.get('enabled.html'):
        tpl = bpy.data.texts.new('enabled.html')
        tpl.from_string('''


<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta
      name="viewport"
      content="width=device-width, initial-scale=1.0, minimum-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover"
    />
    <meta http-equiv="X-UA-Compatible" content="ie=edge" />
    <title>enable3d • 3D for Web, Mobile and PC</title>
    <meta name="description" content="enabled3d" />
    <link rel="stylesheet" href="./enabled/css/style.css" />
    	<style>
  .button-container {
    position: absolute;
    z-index: 999;
    left: 0;
    top: 10px;
  }

  .button {
    display: inline-block;
    padding: 5px 16px;
    font-size: 16px;
    text-align: center;
    text-decoration: none;
    background-color: #4CAF50; /* Green background */
    color: white; /* White text color */
    border: 1px solid #4CAF50; /* Green border */
    border-radius: 5px; /* Rounded corners */
    cursor: pointer;
  }
  .btnred{
    background-color: red;
  }
  .button:hover {
    background-color: #45a049; /* Darker green on hover */
  }
</style>
  </head>

  <body>
   

     <div id="welcome-game">
      <div id="welcome-game-placeholder">
        <div id="welcome-game-placeholder-loader"><div class="loader"></div></div>
        <div id="welcome-game-placeholder-image"></div>
      </div>
    </div>
	
    <div style="position:absolute;z-index:999;left:0;top:10px">
<a href="enabled.html" class="button btnred">Fps</a>
<a href="http://localhost:8001/" class="button">Viewer</a>

 <a href="ar.html" class="btn btn-success button" >AR</a>
</div>
    
    
    CAN BE CUSTOMIZED USING THE enabled3d LIBRARY. for special requests sukuratac@gmail.com
    
    
  </body>
</html>

     
''')




def default_template_R():
    if not bpy.data.texts.get('render.html'):
        tpl = bpy.data.texts.new('render.html')
        tpl.from_string('''

<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Path Tracing Renderer - Test Scene</title>
  <script src="https://cdn.jsdelivr.net/npm/three@0.108.0/build/three.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/three@0.108.0/examples/js/loaders/GLTFLoader.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/three@0.108.0/examples/js/controls/OrbitControls.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/three@0.108.0/examples/js/loaders/RGBELoader.js"></script>

  <script src="https://cdn.jsdelivr.net/npm/three@0.108.0/examples/js/libs/dat.gui.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/three@0.108.0/examples/js/lights/RectAreaLightUniformsLib.js"></script>
   <script src="https://www.3dartasarim.com/3dweb/webrender/editor/ray-tracing-renderer/build/RayTracingRenderer.js"></script>
 
 <link type="text/css" rel="stylesheet" href="bluebutton.css">
 

   <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.4.1/css/bootstrap.min.css">
  <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.7.1/jquery.min.js"></script>
  <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.4.1/js/bootstrap.min.js"></script>
	
  <style>
    html, body {
		 margin: 0px;
		overflow: hidden;
      padding: 0;
      width: 100%;
      height: 100%;
    }

    canvas {
      display: block;
    }

    #loading {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
    }
	
.rounded-rect {
background: white;
border-radius: 10px;
box-shadow: 0 0 50px -25px black;
}
 
.flex-center {
position: absolute;
display: flex;
justify-content: center;
align-items: center;
}
 
.flex-center.left {
left: 0px;
}
 
.flex-center.right {
right: 0px;
}
 
.sidebar-content {
position: absolute;
width: 95%;
height: 95%;
font-family: Arial, Helvetica, sans-serif;
font-size: 32px;
color: gray;
}
 
.sidebar-toggle {
position: absolute;
width: 1.3em;
height: 1.3em;
overflow: visible;
display: flex;
justify-content: center;
align-items: center;
}
 
.sidebar-toggle.left {
right: -1.5em;
}
 
.sidebar-toggle.right {
left: -1.5em;
}
 
.sidebar-toggle:hover {
color: #0aa1cf;
cursor: pointer;
}
 
.sidebar {
transition: transform 1s;
z-index: 1;
width: 300px;
height: 100%;
}
 
/*
The sidebar styling has them "expanded" by default, we use CSS transforms to push them offscreen
The toggleSidebar() function removes this class from the element in order to expand it.
*/
.left.collapsed {
transform: translateX(-295px);
}
 
.right.collapsed {
transform: translateX(295px);
}
  </style>
</head>

<body>
	
<div id="container" style="position:absolute;z-index:1;left:0;top:0">
    
  </div> 
 <div class="dropdown" style="position:absolute;z-index:9999;top:3px;left:3px">
		 <span style="display:none"><a href="enabled.html"  class="btn btn-success ">Fps</a>
		<a href="http://localhost:8001/" class="btn btn-success ">Viewer</a>
		<a href="#render.html" class="btn btn-success " id="exporter">Render</a>
        <a href="ar.html" class="btn btn-success button" >AR</a>
		</span>
  <button class="btn btn-primary dropdown-toggle" type="button" data-toggle="dropdown">HDR LİSTS
  <span class="caret"></span></button>
  <ul class="dropdown-menu" id="lists">
   
  
  </ul>
</div>

	
	
	
		<div id="right"  class="sidebar flex-center right collapsed" style="">
		<div class="sidebar-content rounded-rect ">
		<br><br>
		
		
		<hr>
		
		
		<button type="button"  id="dcolrough" class="dcc" title="envMap"  value="0"  style="color:red">Roughness</button>
		
<br>

	<HR>
	
	
	 <i id="soladon"  style="cursor:pointer" class="btn btn-info glyphicon glyphicon-menu-left" class="dcc" title="envMap"></i>Round<i style="cursor:pointer" id="sagadon" class="btn btn-info glyphicon glyphicon-menu-right"></i>
	<hr>

			
		
		<div class="sidebar-toggle rounded-rectr right" class="dcc" title="envMap" onclick="toggleSidebar('right')" style="top:90px">
		<i id="mnuleftright" style="color:teal" class="glyphicon glyphicon-cog"></i>
		</div>
		
		
		</div>
		
		</div>
		
		
<button style="position:absolute;z-index:99;left:33%;bottom:45%;color:red" type="button"  id="ray"  value="0" >Start Render</button>
<img id="shot"  src="img.png" style="cursor:pointer;right:2px;position:absolute;z-index:11;bottom:72px;margin-left:3px;background-color:white;width:43px;height:43px;border-radius:5px;"/>	

<div id="info" style="padding:5px;border-radius:11px;display:none;height:300px;width:250px;background-color:white;position:absolute;z-index:99999999;top:7px">

	<button id="kapatss">x</button>
		<div class="container" style="height:280px;width:250px;overflow:scroll">
				<img src="" id="sht">
		</div>

	</div>
			
			
  <h1 id="loading">Loading...</h1>
  <script>
  
  
  
  
function getHdrFromUrl() {
  const urlFragment = window.location.href; // # işaretinden sonrasını al

console.log(urlFragment);
  // Varsayılan değer
  let hdr = 'env/venice_sunset_1k.hdr';

  // URL'den hdr parametresini al
  if (urlFragment.includes('hdr=')) {
  console.log(urlFragment);
    hdr = urlFragment.split('=')[1].split('&')[0];
  }

  return hdr;
}

// Kullanım örneği
const hdr = getHdrFromUrl();



  const blobFragment = window.location.href; // # işaretinden sonrasını al


   var  blob=blobFragment.split('=')[2];
 
console.log(blob);

document.getElementById('lists').innerHTML='<li><a class="dropdown-item selecthdr" href="render.html?hdr=env/brown_photostudio_02_1k.hdr&blob='+blob+'" title="1 hdr">brown photo 2 </a></li><li><a class="dropdown-item selecthdr" href="render.html?hdr=env/brown_photostudio_05_1k.hdr&blob='+blob+'" title="1 hdr">brown photo 1</a></li> <li><a class="dropdown-item selecthdr" href="render.html?hdr=env/royal_esplanade_1k.hdr&blob='+blob+'" title="1 hdr">1 hdr</a></li><li><a class="dropdown-item selecthdr" href="render.html?hdr=env/venice_sunset_1k.hdr&blob='+blob+'" title="sunset">sunset</a></li>';


  const renderer = new THREE.RayTracingRenderer();
renderer.setPixelRatio(1.0);
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.5;
renderer.toneMappingWhitePoint = 5;
renderer.maxHardwareUsage = true;
renderer.renderWhenOffFocus = false;

document.body.appendChild(renderer.domElement);

 const model = new THREE.Object3D();


const camera = new THREE.LensCamera(40, window.innerWidth / window.innerHeight, 0.1, 1000 );

const controls = new THREE.OrbitControls(camera, renderer.domElement);
controls.screenSpacePanning = true;

const scene = new THREE.Scene();

	
		

function resize() {
  if (renderer.domElement.parentElement) {
    const width = renderer.domElement.parentElement.clientWidth;
    const height = renderer.domElement.parentElement.clientHeight;
    renderer.setSize(width, height);

    camera.aspect = width / height;
    camera.updateProjectionMatrix();
  }
}

window.addEventListener('resize', resize);
resize();

const tick = (time) => {
  controls.update();
  camera.focus = controls.target.distanceTo(camera.position);

  renderer.sync(time);
  renderer.render(scene, camera);

  requestAnimationFrame(tick);
};

const geo = new THREE.SphereBufferGeometry(1, 24, 24);

function makeMesh() {
  const mat = new THREE.RayTracingMaterial();
  const mesh = new THREE.Mesh(geo, mat);

  // test setting scale and position on mesh
  mesh.position.set(0, 4, 0);
  mesh.scale.set(4, 4, 4);
  return mesh;
}




function init() {
	
	
  const envmap = new THREE.RGBELoader().load(hdr);
  
  const envLight = new THREE.EnvironmentLight(envmap);
  scene.add(envLight);
  
 
  controls.target.set(0, 0, 0);
  camera.position.set(0, 2, 5);




  // test box with .visible set to false
  // should not be visible in the scene
  {
    const geo = new THREE.BoxBufferGeometry(5, 5, 5);
    const mat = new THREE.MeshStandardMaterial();
    const mesh = new THREE.Mesh(geo, mat);
    mesh.position.set(0, 10, 0);
    mesh.visible = false;
    model.add(mesh);
  }

  scene.add(model);
var m;
var objectLoader = new THREE.GLTFLoader();
				objectLoader.load( blob, function ( gltf ) {
	m=gltf.scene;
	m.name='models';
				 	scene.add( m  );

				});
	
	
				
document.querySelector( '#soladon' ).addEventListener( 'click', () => {
                     
			scene.getObjectByName('models').position.x=20;		    
   
  
				}) ;
	
	 document.getElementById("ray").addEventListener('click', ray);
  
 function ray() {

console.log('render starting');
    document.querySelector('#ray').remove();
  
}
  
	
document.querySelector( '#sagadon' ).addEventListener( 'click', () => {

			 scene.rotateY(0.1);
				
				}) ;
		
		
	
   document.getElementById("shot").addEventListener('click', takeScreenshot);
  const infoDiv = document.getElementById('info');

 function takeScreenshot() {

    // open in new window like this
  
    var img = new Image();
    // Without 'preserveDrawingBuffer' set to true, we must render now
    renderer.render(scene, camera);
    img.src = renderer.domElement.toDataURL();
   
document.getElementById('sht').src=img.src;
    renderer.domElement.toBlob(function(blob){
    	var a = document.createElement('a');
      var url = URL.createObjectURL(blob);
      a.href = url;
      a.download = 'canvas.png';
      a.click();
    }, 'image/png', 1.0);

     infoDiv.style.display = 'block'; 
}
  		

infoDiv.style.display = 'none'; 

// Düğmeye tıklandığında
document.getElementById('kapatss').addEventListener('click', function() {
  
  infoDiv.style.display = 'none'; 
});



        
  THREE.DefaultLoadingManager.onLoad = () => {

    

    THREE.DefaultLoadingManager.onLoad = undefined;
    tick();
	 document.querySelector('#loading').remove();
  
  };
}

init();

  </script>
</body>
</html>

     
''')


def default_template_modelwiever():
    if not bpy.data.texts.get('ar.html'):
        tpl = bpy.data.texts.new('ar.html')
        tpl.from_string('''

<html lang="en"><head>

    <title>model-viewer</title>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">
  
		<script src="https://code.jquery.com/jquery-2.1.3.js"></script>
		<link rel="stylesheet" href="https://code.jquery.com/mobile/1.4.5/jquery.mobile-1.4.5.min.css" />
		
		<script src="https://code.jquery.com/mobile/1.4.5/jquery.mobile-1.4.5.js"></script>	
	  
	  CAN BE CUSTOMIZED USING THE >model-viewer LIBRARY. for special requests: sukuratac@gmail.com


</body></html>

     
''')


class threejsExportPanel_PT_Panel(bpy.types.Panel):
    bl_idname = "threejs_EXPORT_PT_Panel"
    bl_label = "B2W Exporter (v 0.0.11)"
    bl_category = "B2W"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, content):
        scene = content.scene
        layout = self.layout
        layout.use_property_split=True
        layout.use_property_decorate = False
        #col = layout.column(align=False)
        #col = layout.column(align=True)
        #row = col.row()
        #col.label(text="Exporter Settings", icon='NONE')
        row = layout.row(align=True)        
        row.prop(scene, 'b_settings', text= "", icon="TRIA_DOWN" if getattr(scene, 'b_settings') else "TRIA_RIGHT", icon_only=False, emboss=False)
        row.label(text="threejs", icon='NONE')
        if scene.b_settings:
            row = layout.row(align=True)
            box = row.box()
            #box.alignment = 'EXPAND'
            box.prop(scene, "s_threejs_version")
            #col.prop(scene, "b_hands")
                
   
            #col.prop(scene, "b_blender_lights")
            box.prop(scene, "b_cast_shadows")
            box.prop(scene, "b_use_default_lights")
            box.separator()
        
                
            
            
        row = layout.row(align=True)      

           
        row.prop(scene, 'b_export', text= "", icon="TRIA_DOWN" if getattr(scene, 'b_export') else "TRIA_RIGHT", icon_only=False, emboss=False)
        row.label(text="Exporter", icon='NONE')
        if scene.b_export:
            row = layout.row(align=True)   
            box = row.box()            
            box.prop(scene, "s_project_name")
            box.prop(scene, "export_path")
            box.prop(scene, "b_export_single_model")
            box.operator('threejs.clear_asset_dir', text='Clear Assets Directory')
        
        # Show properties of selected object
        
        row = layout.row(align=True) 
        row.label(text="Selected Object Properties", icon='NONE')
        row = layout.row(align=True)   
        box = row.box()        

                  

        row = layout.row(align=True) 
        row.operator('threejs.export', text='Export threejs Project')
        row = layout.row(align=True) 
        serve_label = "Stop Serving" if Server.instance else "Start Serving"
        row.operator('threejs.serve', text=serve_label)
        row = layout.row(align=True) 
        if Server.instance:
            row.operator("wm.url_open", text="Open Preview").url = f'http://localhost:{PORT}'
            row = layout.row(align=True) 
        row.label(text=scene.s_output, icon='INFO')
        


class threejsClean_OT_Operator(bpy.types.Operator):
    bl_idname = "threejs.clean"
    bl_label = "Clean"
    bl_description = "Clean"
        
    def execute(self, content):
        # TODO checkout is add-on is present
        bpy.ops.tlm.clean_lightmaps("INVOKE_DEFAULT")
        print("cleaning baked lightmaps")
        return {'FINISHED'}   
   

class threejsClearAsset_OT_Operator(bpy.types.Operator):
    bl_idname = "threejs.clear_asset_dir"
    bl_label = "Crear Asset Directory"
    bl_description = "Crear Asset Directory"
    
    def execute(self, content):
        scene = content.scene
        DEST_RES = os.path.join ( scene.export_path, scene.s_project_name )

        # Clear existing "assests" directory
        assets_dir = os.path.join ( DEST_RES, PATH_ASSETS )
        if os.path.exists( assets_dir ):
            shutil.rmtree( assets_dir )
        return {'FINISHED'}

class threejsPrepare_OT_Operator(bpy.types.Operator):
    bl_idname = "threejs.prepare"
    bl_label = "Prepare for Ligthmapper"
    bl_description = "Prepare Lightmapper"
    
    def execute(self, content):
        scene = content.scene
        DEST_RES = os.path.join ( scene.export_path, scene.s_project_name )
        bpy.context.scene.TLM_SceneProperties.tlm_mode = 'GPU'
        view_layer = bpy.context.view_layer
        obj_active = view_layer.objects.active
        selection = bpy.context.selected_objects

        bpy.ops.object.select_all(action='SELECT')
        bpy.context.view_layer.objects.active = obj_active
        for obj in selection:
            obj.select_set(True)
            # some exporters only use the active object
            view_layer.objects.active = obj
            bpy.context.object.TLM_ObjectProperties.tlm_mesh_lightmap_use = True
            bpy.context.object.TLM_ObjectProperties.tlm_mesh_lightmap_resolution = '256'
        
        return {'FINISHED'}

class threejsClear_OT_Operator(bpy.types.Operator):
    bl_idname = "threejs.delete_lightmap"
    bl_label = "Delete generated lightmaps"
    bl_description = "Delete Lightmaps"
    
    def execute(self, content):
        scene = content.scene
        DEST_RES = os.path.join ( scene.export_path, scene.s_project_name )
        
        # delete all _baked textures
        images = bpy.data.images
        for img in images:
            if "_baked" in img.name:
                print("[CLEAR] delete image "+img.name)
                bpy.data.images.remove(img)
        
        #for material in bpy.data.materials:
        #    material.user_clear()
        #    bpy.data.materials.remove(material)
        
        for filename in os.listdir(os.path.join ( DEST_RES, PATH_LIGHTMAPS)):
            os.remove(os.path.join ( DEST_RES, PATH_LIGHTMAPS) + filename)
        
        #if os.path.exists(os.path.join(DEST_RES, PATH_LIGHTMAPS)):
        #    shutil.rmtree(os.path.join(DEST_RES,PATH_LIGHTMAPS))
        #bpy.ops.tlm.build_lightmaps()

        return {'FINISHED'}


class threejsLoadlm_OT_Operator(bpy.types.Operator):
    bl_idname = "threejs.loadlm"
    bl_label = "load lightmaps"
    bl_description = "Load Lightmaps"
    
    def execute(self, content):
        scene = content.scene
        DEST_RES = os.path.join ( scene.export_path, scene.s_project_name )
        
        # delete all _baked textures
        images = bpy.data.images
        for img in images:
            if "_baked" in img.name:
                print("delete: "+img.name)
                bpy.data.images.remove(img)
                
        for filename in os.listdir(os.path.join ( DEST_RES, PATH_LIGHTMAPS)):
            bpy.data.images.load(os.path.join ( DEST_RES, PATH_LIGHTMAPS) + filename)
        return {'FINISHED'}    
        
class threejsServe_OT_Operator(bpy.types.Operator):
    bl_idname = "threejs.serve"
    bl_label = "Serve threejs Preview"
    bl_description = "Serve threejs"
    
    def execute(self, content):
        if (Server.instance):
            Server.instance.stop()
            Server.instance = None
            return {'FINISHED'}
        scene = content.scene
        Server.instance = Server()
        Server.instance.set_folder(os.path.join ( scene.export_path, scene.s_project_name ))
        Server.instance.start()
        
        return {'FINISHED'}

class threejsExport_OT_Operator(bpy.types.Operator):
    bl_idname = "threejs.export"
    bl_label = "Export to threejs Project"
    bl_description = "Export threejs"

    def execute(self, content):
        assets = []
        entities = []
        lights = []
        print("[threejs EXPORTER] Starting Exporting Project.....................................")
        scene = content.scene
        scene.s_output = "exporting..."
        script_file = os.path.realpath(__file__)
        #print("script_file dir = "+script_file)
        directory = os.path.dirname(script_file)

        # Destination base path
        DEST_RES = os.path.join ( scene.export_path, scene.s_project_name )


        if __name__ == "__main__":
            #print("inside blend file")
            #print(os.path.dirname(directory))
            directory = os.path.dirname(directory)

        print("[threejs EXPORTER] Target Output Directory = "+directory)

        ALL_PATHS = [ ".", PATH_ASSETS, PATH_RESOURCES, PATH_MEDIA, PATH_BUILD,PATH_JAVASCRIPT_LOADERS,PATH_JAVASCRIPT_EXPORTERS, PATH_JAVASCRIPT_CONTROLS,PATH_JAVASCRIPT_LIBS,PATH_ENV, PATH_LIGHTMAPS,PATH_ENABLED_DIR,PATH_ENABLED_JS,PATH_ENABLED_LIB,PATH_ENABLED_LIB_MOZ ]
        for p in ALL_PATHS:
            dp = os.path.join ( DEST_RES, p )
            print ( "--- DEST [%s] [%s] {%s}" % ( DEST_RES, dp, p ) )
            os.makedirs ( dp, exist_ok=True )

        #check if addon or script for correct path
        _resources = [
            [ ".", "favicon.ico", True ],
            [ ".", "style.css" , True],
            [ ".", "main.css" , True],
            [ ".", "start_web_server.py" , False],
            [ PATH_RESOURCES, "play.png", False ],
            [ PATH_RESOURCES, "pause.png", False],
            [ PATH_ENV, "venice_sunset_1k.hdr",True ],
            [ PATH_ENV, "royal_esplanade_1k.hdr",True ],
            [ PATH_MEDIA, "image2.png",False ],                        
            [ PATH_JAVASCRIPT_CONTROLS, "OrbitControls.js", True ],
            [ PATH_JAVASCRIPT_LOADERS, "GLTFLoader.js", True ],
            [PATH_JAVASCRIPT_EXPORTERS, "GLTFExporter.js", True ],
            [ PATH_JAVASCRIPT_LOADERS, "RGBELoader.js", True ],
            [ PATH_JAVASCRIPT_LIBS, "lil-gui.module.min.js", True ],
            [ PATH_BUILD, "three.module.js", True ],
            [ PATH_ENABLED_JS,"load-images.js",True],
            [ PATH_ENABLED_LIB,"enable3d.framework.0.25.4.min.js",True],
            [ PATH_ENABLED_LIB_MOZ,"ammo.js",True],
            [ PATH_ENABLED_LIB_MOZ,"ammo.wasm.js",True],
            [ PATH_ENABLED_LIB_MOZ,"ammo.wasm.wasm",True]
            
            
        ]

        SRC_RES = os.path.join ( directory, PATH_RESOURCES )
        for dest_path, fname, overwrite in _resources:
            if overwrite:
                shutil.copyfile ( os.path.join ( SRC_RES, fname ), os.path.join ( DEST_RES, dest_path, fname ) )
            else:
                if not os.path.exists(os.path.join ( DEST_RES, dest_path, fname )):
                    shutil.copyfile ( os.path.join ( SRC_RES, fname ), os.path.join ( DEST_RES, dest_path, fname ) )                    

        # Loop 3D entities
        exclusion_obj_types = ['CAMERA','LAMP','ARMATURE']
        exported_obj = 0
        videocount=0
        imagecount=0
        scalefactor = 2
        lightmap_files = os.listdir(os.path.join ( DEST_RES, PATH_LIGHTMAPS))
        for file in lightmap_files:
            print("[LIGHTMAP] Found Lightmap file: "+file)

        # ONE SINGLE MESH
        # Note: with a single mesh you can't add interactions
        if scene.b_export_single_model:
            print("[threejs EXPORTER] Exporting one single global mesh")
            if scene.b_cast_shadows:
                single_cast_shadows = "true"
            else:                     
                single_cast_shadows = "false"
            
            entities.append('{path: "./assets/MainMesh.gltf", position: [0,0,0],name: "MainMesh"}')
            exported_obj+=1
            bpy.ops.object.select_all(action='SELECT')
            filename = os.path.join ( DEST_RES, PATH_ASSETS, "MainMesh" ) # + '.glft' )
#            bpy.ops.export_scene.gltf(filepath=filename, export_format='GLTF_EMBEDDED', use_selection=True)
#            obj.select_set(state=True)
            bpy.ops.export_scene.gltf(filepath=filename, export_format='GLTF_EMBEDDED', use_selection=True, export_texcoords = True, export_normals = True, export_draco_mesh_compression_enable = False, export_draco_mesh_compression_level = 6, export_draco_position_quantization = 14, export_draco_normal_quantization = 10, export_draco_texcoord_quantization = 12, export_draco_generic_quantization = 12,export_tangents = True, export_materials = 'EXPORT', export_colors = True, export_extras = True, export_yup = True, export_apply = True, export_animations = True, export_frame_range = True, export_frame_step = 1, export_force_sampling = True)
            bpy.ops.object.select_all(action='DESELECT')
        else:
            # MULTI MESH EXPORTING
            for obj in bpy.data.objects:
                if obj.type not in exclusion_obj_types:
                    print("[threejs EXPORTER] loop object "+ obj.name)
                    bpy.ops.object.select_all(action='DESELECT')
                    obj.select_set(state=True)
                    bpy.context.view_layer.objects.active = obj
                    #bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS', center='BOUNDS')
                    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')
                    location = obj.location.copy()
                    rotation = obj.rotation_euler.copy()
                    
                    bpy.ops.object.location_clear()
                    actualposition = str(location.x)+","+str(location.z)+","+str(location.y)
                    actualscale = str(scalefactor*bpy.data.objects[obj.name].scale.x)+" "+str(scalefactor*bpy.data.objects[obj.name].scale.z)+" "+str(scalefactor*bpy.data.objects[obj.name].scale.y)
                    #pi = 22.0/7.0
                    #actualrotation = str(((bpy.data.objects[obj.name].rotation_euler.x) / (2 * pi) * 360) - 90) +" " + str(((bpy.data.objects[obj.name].rotation_euler.z) / (2 * pi) * 360)-0) + " " + str(((bpy.data.objects[obj.name].rotation_euler.y) / (2 * pi) * 360)+90)
                    #actualrotation = str(bpy.data.objects[obj.name].rotation_euler.x) +" " + str(bpy.data.objects[obj.name].rotation_euler.z)+ " " + str(bpy.data.objects[obj.name].rotation_euler.y)
                    #actualrotation = str(math.degrees(-89.99+bpy.data.objects[obj.name].rotation_euler.x)) +" " + str(90+math.degrees(bpy.data.objects[obj.name].rotation_euler.y))+ " " + str(-90+math.degrees(bpy.data.objects[obj.name].rotation_euler.z))
                    #actualrotation = str(math.degrees(rotation.x))+" "+str(math.degrees(rotation.z))+" "+str(math.degrees(-rotation.y))    
                    actualrotation = "0 "+str(math.degrees(rotation.z))+" 0"    
                        
                    # custom threejs code read from CUSTOM PROPERTIES
                    reflections = ""
                    animation = ""
                    baked = ""
                    custom = ""
                    toggle = ""
                    video = False
                    image = False
                    tag = "entity"
                    gltf_model = 'gltf-model="#'+obj.name+'"' 

                    # export gltf
                    # print(obj.type)
                    if obj.type == 'MESH' or obj.type == 'EMPTY':
                        if obj.type == 'EMPTY':
                            gltf_model = ''
                        #print(obj.name,"custom properties:\n********************")                        
                        

                        if video == False and image == False:                        
                            # check if baked texture is present on filesystem
                            #images = bpy.data.images
                            #for img in images:
                            #    if obj.name+"_baked" in img.name and img.has_data:
                            #       print("ok")
                            #       baked = 'light-map-geometry="path: lightmaps/'+img.name+'"'
                            print("[LIGHTMAP] Searching Lightmap for object ["+obj.name+"_baked"+"]")                        
                            for file in lightmap_files:
                                if obj.name+"_baked" in file:
                                    print("[LIGHTMAP] Found lightmap: "+file)
                                    baked = 'light-map-geometry="path: lightmaps/'+file+'; intensity: '+str(scene.f_lightMapIntensity)+'"'
                                
                            filename = os.path.join ( DEST_RES, PATH_ASSETS, obj.name ) # + '.glft' )
                            #bpy.ops.export_scene.gltf(filepath=filename, export_format='GLTF_EMBEDDED', use_selection=True)
                            bpy.ops.export_scene.gltf(filepath=filename, export_format='GLTF_EMBEDDED', use_selection=True, export_texcoords = True, export_normals = True, export_draco_mesh_compression_enable = False, export_draco_mesh_compression_level = 6, export_draco_position_quantization = 14, export_draco_normal_quantization = 10, export_draco_texcoord_quantization = 12, export_draco_generic_quantization = 12,export_tangents = True, export_materials = 'EXPORT', export_colors = True, export_extras = True, export_yup = True, export_apply = True, export_animations = True, export_frame_range = True, export_frame_step = 1, export_force_sampling = True)
                            assets.append('\'./assets/'+obj.name +'.gltf\',')
                            if scene.b_cast_shadows:
                                entities.append('{path: "./assets/'+obj.name + '.gltf", position: ['+actualposition+'],name: "' + obj.name + '"},')
                            else:
                                entities.append('{path: "./assets/'+obj.name + '.gltf", position: ['+actualposition+'],name: "' + obj.name + '"},')
                    # deselect object
                    obj.location = location
                    obj.select_set(state=False)
                    exported_obj+=1

        # Loop the Lamps
        print('[LAMPS] Searching for lamps in scene')
        lamp_types = ['LIGHT']
        blender_lights = []
        for obj in bpy.data.objects:
#            print(obj.name, ' = ', obj.type)
            if obj.type in lamp_types:
                #print(obj.name, obj.data.type, obj.data.color, obj.data.distance, obj.data.cutoff_distance, str(obj.location.x)+" "+str(obj.location.z)+" "+str(-obj.location.y))    
                distance = str(obj.data.distance)
                hex_color = to_hex(obj.data.color)
                
                light_type = "Directional"
                if obj.data.type == "POINT":
                    light_type = "Point"
                elif obj.data.type == "SUN":
                    light_type = "Directional"
                elif obj.data.type == "SPOT":
                    light_type = "Spot"
                light_position = str(obj.location.x)+","+str(obj.location.z)+","+str(obj.location.y)                    
                cutoff_distance = str(obj.data.cutoff_distance)
                intensity = str(obj.data.energy)
                if scene.b_cast_shadows:
                    cast_shadows = "true"
                else:                     
                    cast_shadows = "true"
                blender_lights.append('{ position:['+light_position+'], light:{castShadow:'+str(cast_shadows)+', color:new THREE.Color("'+hex_color+'"), distance:'+cutoff_distance+', type:"'+light_type+'", intensity:'+intensity+', shadowBias: -0.001, shadowCameraFar: 501.02, shadowCameraBottom: 12, shadowCameraFov: 101.79, shadowCameraNear: 0, shadowCameraTop: -5, shadowCameraRight: 10, shadowCameraLeft: -10, shadowRadius: 2}},')
        #print(blender_lights)
        # Loop the Lamps

        print("[threejs EXPORTER] Completed Exporting Project.....................................")

        bpy.ops.object.select_all(action='DESELECT')

        # Templating ------------------------------
        #print(assets)
        all_assets = ""
        for x in assets:
            all_assets += x

        all_entities = ""
        for y in entities:
            all_entities += y



        #shadows
        if scene.b_cast_shadows:
            showcast_shadows = "true"
            template_render_shadows = 'shadow="type: pcfsoft; autoUpdate: true;"'            
        else:
            showcast_shadows = "false"
            template_render_shadows = 'shadow="type: basic; autoUpdate: false;"'            

        # if use bake, the light should have intensity near zero
        if scene.b_use_lightmapper:
            light_directional_intensity = "0"
            light_ambient_intensity = "0.1"
        else:
            light_directional_intensity = "1.0"
            light_ambient_intensity = "1.0"

        if scene.b_use_default_lights:
            final_lights = '<a-entity light="intensity: '+ light_directional_intensity+'; castShadow: '+showcast_shadows+'; shadowBias: -0.001; shadowCameraFar: 501.02; shadowCameraBottom: 12; shadowCameraFov: 101.79; shadowCameraNear: 0; shadowCameraTop: -5; shadowCameraRight: 10; shadowCameraLeft: -10; shadowRadius: 2" position="1.36586 7.17965 1"></a-entity>\n\t\t\t<a-entity light="type: ambient; intensity: '+light_ambient_intensity+'"></a-entity>'
            #print("final lights="+final_lights)
        else:
            templights = ""
            for x in blender_lights:
                templights += x           
            final_lights = templights

       
        default_template()
        t = Template( bpy.data.texts['index.html'].as_string() )
        s = t.substitute(
            asset=all_assets,
            entity=all_entities,
            threejs_version=scene.s_threejs_version,
            cast_shadows=showcast_shadows,
            render_shadows=template_render_shadows,
            lights=final_lights)

        default_template_enabled()
        te = Template( bpy.data.texts['enabled.html'].as_string() )
        se = te.substitute(
            asset=all_assets,
            entity=all_entities,
            threejs_version=scene.s_threejs_version,
            cast_shadows=showcast_shadows,
            render_shadows=template_render_shadows,
            lights=final_lights)
            
        default_template_R()
        teR = Template( bpy.data.texts['render.html'].as_string() )
        seR = teR.substitute(
            asset=all_assets,
            entity=all_entities,
            threejs_version=scene.s_threejs_version,
            cast_shadows=showcast_shadows,
            render_shadows=template_render_shadows,
            lights=final_lights)
            
        default_template_modelwiever()
        teRm = Template( bpy.data.texts['ar.html'].as_string() )
        seRm = teRm.substitute(
            asset=all_assets,
            entity=all_entities,
            threejs_version=scene.s_threejs_version,
            cast_shadows=showcast_shadows,
            render_shadows=template_render_shadows,
            lights=final_lights)
        
        #print(s)

        # Saving the main INDEX FILE
        with open( os.path.join ( DEST_RES, PATH_INDEX ), "w") as file:
            file.write(s)
            
        with open( os.path.join ( DEST_RES, PATH_ENABLED ), "w") as file:
            file.write(se)
            
        with open( os.path.join ( DEST_RES, PATH_INDEX_RENDERED ), "w") as file:
            file.write(seR)
        
        with open( os.path.join ( DEST_RES, PATH_INDEX_AR ), "w") as file:
            file.write(seRm)
            
        scene.s_output = str(exported_obj)+" meshes exported"
        self.report({'INFO'}, str(exported_obj)+" meshes exported")
        return {'FINISHED'}


# ------------------------------------------- REGISTER / UNREGISTER
_props = [
    ("str", "s_threejs_version", "threejs version", "threejs version", "1.2.0" ),
    ("bool", "b_hands", "Use Hands Models", "Use hands models instead of controllers", True ),
    ("bool", "b_blender_lights", "Export Blender Lights", "Export Blenedr Lights or use threejs default ones" ),
    ("bool", "b_cast_shadows", "Cast Shadows", "Cast and Receive Shadows" ),
    ("bool", "b_use_default_lights", "Don't export Blender lights", "Use Default Lights - don't export blender lights" ),
    ("bool", "b_lightmaps", "Use Lightmaps as Occlusion (GlTF Settings)", "GLTF Models don\'t have lightmaps: turn on this option will save lightmaps to Ambient Occlusion in the GLTF models" ),
    ("float", "f_raycast_length", "Raycast Length","Raycast lenght to interact with objects", 10.0 ),
    ("float", "f_raycast_interval", "Raycast Interval","Raycast Interval to interact with objects", 1500.0 ),
    ("str", "export_path", "Export To","Path to the folder containing the files to import", "C:/Temp/", 'FILE_PATH'),
    ("bool", "b_export_single_model", "Export to a single glTF model","Export to a single glTF model", True),
    ("str", "s_project_name", "Name", "Project's name","threejs-prj"),
    ("str", "s_output", "output","output export","output"),
    ("bool", "b_use_lightmapper", "Use Lightmapper Add-on","Use Lightmapper for baking" ),
    ("bool", "b_raycast", "Enable Raycast","Enable Raycast"),
    ("bool", "b_settings", "threejs settings","b_settings"),
    ("bool", "b_interactive", "Interactive","b_interactive"),        
    ("bool", "b_export", "Exporter settings","b_export"),    
    ("bool", "b_bake", "Bake settings","b_bake"),         
    ("bool", "b_bake_lightmap", "Bake settings","b_bake_lightmap"),     
    ("float", "f_lightMapIntensity", "LightMap Intensity","LightMap Intensity", 2.0),               
    ("bool", "b_aa", "Antialiasing","Antialiasing"),    
    ("bool", "b_colorManagement", "Color Management","ColorManagement"),        
    ("bool", "b_physicallyCorrectLights", "Physically Correct Lights","PhysicallyCorrectLights"),         
]

# CUSTOM PROPERTY OPERATORS
class DeleteProperty(bpy.types.Operator):
    bl_idname = 'threejs.delete_property'
    bl_label = 'Remove'
    bl_description = 'Remove custom property from selected object'

    targetproperty: bpy.props.StringProperty(name="targetproperty")

    def execute(self, context):
        try:
            scene = context.scene
            print("deleting:" , self.targetproperty)
            del bpy.context.active_object[self.targetproperty]
        except Exception as e:
            bpy.ops.wm.popuperror('INVOKE_DEFAULT', e = str(e))
        return {'FINISHED'}


    
class Images(bpy.types.Operator):
    bl_idname = 'threejs.images'
    bl_label = 'Add Toggle Images'
    bl_description = 'Add two toggle images for selected object'
    def execute(self, context):
        try:
            bpy.context.active_object["threejs_IMAGES"] = '{"1": "image1.png", "2": "image2.png"}'
        except Exception as e:
            bpy.ops.wm.popuperror('INVOKE_DEFAULT', e = str(e))
        return {'FINISHED'}







def _reg_bool ( scene, prop, name, descr, default = False ):
    setattr ( scene, prop, bpy.props.BoolProperty ( name = name, description = descr, default = default ) )

def _reg_str ( scene, prop, name, descr, default = "", subtype = "" ):
    if subtype:
        setattr ( scene, prop, bpy.props.StringProperty ( name = name, description = descr, default = default, subtype = subtype ) )
    else:
        setattr ( scene, prop, bpy.props.StringProperty ( name = name, description = descr, default = default ) )


def _reg_float ( scene, prop, name, descr, default = 0.0 ):
    setattr ( scene, prop, bpy.props.FloatProperty ( name = name, description = descr, default = default ) )

def register():
    scn = bpy.types.Scene

    bpy.utils.register_class(threejsExportPanel_PT_Panel)

    bpy.utils.register_class(threejsClean_OT_Operator)
    bpy.utils.register_class(threejsExport_OT_Operator)
    bpy.utils.register_class(threejsServe_OT_Operator)

    bpy.utils.register_class(threejsClear_OT_Operator)
    bpy.utils.register_class(threejsPrepare_OT_Operator)
    bpy.utils.register_class(threejsClearAsset_OT_Operator)    
 
    bpy.utils.register_class(Images)       
    
                   
    bpy.utils.register_class(DeleteProperty)                       
    
    for p in _props:
        if p [ 0 ] == 'str': _reg_str ( scn, * p [ 1 : ] )
        if p [ 0 ] == 'bool': _reg_bool ( scn, * p [ 1 : ] )
        if p [ 0 ] == 'float': _reg_float ( scn, * p [ 1 : ] )

    # deletes intex.html template embeded file
    #for t in bpy.data.texts:
    #    if (t.name == 'index.html'):
    #        print(t.name)
    #        bpy.data.texts.remove(t)


def unregister():
    if Server.instance:
        Server.instance.stop()
        Server.instance = None

    bpy.utils.unregister_class(threejsExportPanel_PT_Panel)
 
    bpy.utils.unregister_class(threejsClean_OT_Operator)    
    bpy.utils.unregister_class(threejsExport_OT_Operator)
    bpy.utils.unregister_class(threejsServe_OT_Operator)
    bpy.utils.unregister_class(threejsClear_OT_Operator)
    bpy.utils.unregister_class(threejsPrepare_OT_Operator)
    bpy.utils.unregister_class(threejsClearAsset_OT_Operator)    
   
    bpy.utils.unregister_class(Images) 
 
    bpy.utils.unregister_class(DeleteProperty)          

    #for p in _props:
    #    del bpy.types.Scene [ p [ 1 ] ]

    # deletes intex.html template embeded file
    for t in bpy.data.texts:
        if (t.name == 'index.html'):
            #print(t.name)
            bpy.data.texts.remove(t)        


# This allows you to run the script directly from Blender's Text editor
# to test the add-on without having to install it.
if __name__ == "__main__":
    register()

def to_hex(c):
    return '#%02x%02x%02x' % (int(c.r*255),int(c.g*255),int(c.b*255))
