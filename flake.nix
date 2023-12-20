{
 description = "ML packages";

 inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-23.11";

 outputs = { self, nixpkgs }: {

  packages.x86_64-linux = {
     
     pyboy = with nixpkgs.legacyPackages.x86_64-linux;
       python3Packages.buildPythonPackage rec {
         pname = "pyboy";
         version = "1.6.9";
         src = fetchPypi {
           inherit pname version;
           sha256 = "Sj4dfJ24AGgwjMxbL81d1gzsK/enS+eZoPZrN7tl9+A=";
         };
        format = "pyproject";
         
         propagatedBuildInputs = with python3Packages; [ 
           setuptools
           cython_3
           numpy
           pillow
           pysdl2
           pip 
         ] ++ [ SDL2 ];
     };
      
     pettingzoo = with nixpkgs.legacyPackages.x86_64-linux;
       python3Packages.buildPythonPackage rec {
         pname = "pettingzoo";
         version = "1.24.2";
         src = fetchPypi {
           inherit pname version;
           sha256 = "ClhW1H3nirIP7d/axJQJWdyJL2vsySEHJHscOiEMCYQ=";
         };
        format = "pyproject";
         
         propagatedBuildInputs = with python3Packages; [ 
           setuptools
           numpy
           gymnasium
           pip 
         ];
    };

    openskill = with nixpkgs.legacyPackages.x86_64-linux;
       python3Packages.buildPythonPackage rec {
         pname = "openskill";
         version = "5.1.0";
         src = fetchPypi {
           inherit pname version;
           sha256 = "MxVmmKMm7Z/EAHscJ45Msqe0CgjzuM/xDF7Ds5CA+qs=";
         };
        format = "pyproject";
         
         propagatedBuildInputs = with python3Packages; [ 
           pdm-backend 
           setuptools
           pip 
         ] ++ [ pkgs.pdm ];
    };

    pearl = with nixpkgs.legacyPackages.x86_64-linux;
      python3Packages.buildPythonPackage {
        pname = "pearl";
        version = "0.1.0";
        src = fetchFromGitHub {
          owner = "facebookresearch";
          repo = "Pearl";
          rev = "master";
          sha256 = "1jrx4+elldXAsEBsHFKu7w59Z4evCsM/eS9KjZW7kJo=";
        };
        format = "pyproject";
        nativeBuildInputs = [ python3Packages.setuptools ];

        propagatedBuildInputs = with python3Packages; [
          gym
          gymnasium
          numpy
          matplotlib
          pandas
          requests
          pip
          torchWithRocm
          torchvision
          torchaudio
        ];  
    };

    pokegym = with nixpkgs.legacyPackages.x86_64-linux;
      python3Packages.buildPythonPackage {
        pname = "pokegym";
        version = "0.1.9";
        src = ./. ;
        format = "pyproject";
        nativeBuildInputs = [ python3Packages.setuptools ];

        propagatedBuildInputs = with python3Packages; [
          gymnasium
          numpy
        ] ++ [ self.packages.x86_64-linux.pyboy ];  
    };

    pufferlib = with nixpkgs.legacyPackages.x86_64-linux;
      python3Packages.buildPythonPackage {
        pname = "pufferlib";
        version = "0.5.0";
        src = fetchFromGitHub {
          owner = "PufferAI";
          repo = "pufferlib";
          rev = "0.5";
          sha256 = "wftDYMrfEBUeK3SoJuo6B9IYR6Ab7N5K1F3JOdMYLe0=";
        };
        format = "pyproject";
        nativeBuildInputs = with python3Packages; [ setuptools wheel ];

        propagatedBuildInputs = with python3Packages; [
          setuptools
          cython_3
          gym
          gymnasium
          numpy
          pandas
          opencv4
          matplotlib
          scikit-image
          pip
          psutil
          tensorboard
          wandb
          # pydantic
          # ray
          torchWithRocm
          torchvision
          torchaudio
        ] ++ [ 
          self.packages.x86_64-linux.pettingzoo 
          self.packages.x86_64-linux.openskill 
        ];
        prePatch = ''
           substituteInPlace pyproject.toml --replace 'setuptools==65.5.0' 'setuptools'
         '';
        };
     };
  };
}
