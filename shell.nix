{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
    # nativeBuildInputs is usually what you want -- tools you need to run
    nativeBuildInputs = with pkgs.buildPackages; [ 
      virtualenv
      python3Packages.pip
      python3Packages.gymnasium
      python3Packages.numpy
      python3Packages.pysdl2
    ];
}