#!/usr/bin/env python3
"""
GLB/glTFファイルの構成を解析する(調査用)

判定したいこと:
  - 四足リグが実際に生成されているか(ボーン構成)
  - 顎(jaw)ボーンがあるか → 顎回転+音声振幅でリップシンクできるか
  - モーフターゲット(ブレンドシェイプ)があるか → ビセーム方式が使えるか
  - メッシュの規模(ポリゴン数の目安、マテリアル、テクスチャ)

使い方:
  python3 scripts/inspect_glb.py <path-to.glb>
"""
import base64
import json
import os
import struct
import sys


def load_gltf(path):
    """GLB(バイナリ)とglTF(JSON)の両方を読めるようにする"""
    with open(path, "rb") as f:
        head = f.read(4)
        f.seek(0)
        if head == b"glTF":
            magic, version, _ = struct.unpack("<III", f.read(12))
            while True:
                h = f.read(8)
                if len(h) < 8:
                    break
                clen, ctype = struct.unpack("<II", h)
                chunk = f.read(clen)
                if ctype == 0x4E4F534A:  # JSON chunk
                    return json.loads(chunk.decode("utf-8")), version
            raise ValueError("GLBにJSONチャンクが見つからない")
        return json.load(open(path, encoding="utf-8")), None


def main():
    if len(sys.argv) < 2:
        sys.exit("使い方: python3 scripts/inspect_glb.py <path-to.glb>")
    path = sys.argv[1]
    if not os.path.exists(path):
        sys.exit(f"ファイルが見つからない: {path}")

    gltf, version = load_gltf(path)
    size = os.path.getsize(path)

    print(f"\n{'='*60}")
    print(f"ファイル: {path}")
    print(f"サイズ: {size:,} bytes ({size/1024/1024:.2f} MB)")
    if version:
        print(f"GLBバージョン: {version}")
    gen = gltf.get("asset", {}).get("generator", "(不明)")
    print(f"生成元: {gen}")
    print(f"{'='*60}")

    nodes = gltf.get("nodes", [])
    skins = gltf.get("skins", [])
    meshes = gltf.get("meshes", [])
    anims = gltf.get("animations", [])

    print(f"\n■ 全体構成")
    print(f"  ノード数      : {len(nodes)}")
    print(f"  スキン数      : {len(skins)}")
    print(f"  メッシュ数    : {len(meshes)}")
    print(f"  アニメーション: {len(anims)}")
    print(f"  マテリアル数  : {len(gltf.get('materials', []))}")
    print(f"  テクスチャ数  : {len(gltf.get('textures', []))}")

    # --- ポリゴン規模 ---
    accessors = gltf.get("accessors", [])
    tri_total = vert_total = 0
    for m in meshes:
        for p in m.get("primitives", []):
            pos = p.get("attributes", {}).get("POSITION")
            if pos is not None and pos < len(accessors):
                vert_total += accessors[pos].get("count", 0)
            idx = p.get("indices")
            if idx is not None and idx < len(accessors):
                tri_total += accessors[idx].get("count", 0) // 3
    print(f"  頂点数(概算)  : {vert_total:,}")
    print(f"  三角形数(概算): {tri_total:,}")

    # --- ボーン ---
    joints = []
    for skin in skins:
        for ji in skin.get("joints", []):
            if ji < len(nodes):
                joints.append(nodes[ji].get("name", f"<node{ji}>"))

    print(f"\n■ ボーン構成 ({len(joints)}個)")
    if joints:
        for n in joints:
            print(f"    {n}")
    else:
        print("    ボーンなし(リグが適用されていない)")

    # --- 核心判定1: 顎まわり ---
    jaw_keys = ("jaw", "mouth", "chin", "tongue", "lip", "teeth")
    jaw_hits = [n for n in joints if any(k in n.lower() for k in jaw_keys)]
    print(f"\n■ 【核心1】顎・口まわりのボーン")
    if jaw_hits:
        for n in jaw_hits:
            print(f"    ✓ {n}")
        print("    → 顎ボーン回転+音声振幅によるリップシンクが可能")
    else:
        print("    ✗ なし")
        print("    → 顎ボーン方式は不可。プロシージャルな頂点変形か、")
        print("       アーキタイプ側で顔リグを作り込む(方式b)必要がある")

    head_hits = [n for n in joints if "head" in n.lower() or "neck" in n.lower()]
    print(f"\n■ 頭・首ボーン(視線/頷きの制御に使う)")
    print(f"    {head_hits if head_hits else '✗ なし'}")

    # --- 核心判定2: ブレンドシェイプ ---
    morph_count = 0
    morph_names = []
    for m in meshes:
        names = m.get("extras", {}).get("targetNames", [])
        morph_names.extend(names)
        for p in m.get("primitives", []):
            morph_count += len(p.get("targets", []))
    print(f"\n■ 【核心2】モーフターゲット(ブレンドシェイプ)")
    print(f"    個数: {morph_count}")
    if morph_names:
        print(f"    名前: {morph_names}")
        print("    → ビセーム方式のリップシンクが使える可能性がある")
    elif morph_count == 0:
        print("    ✗ なし(事前調査どおり、自動生成では出ない)")

    # --- アニメーション ---
    if anims:
        print(f"\n■ 同梱アニメーション")
        for a in anims:
            print(f"    {a.get('name', '(名称なし)')} "
                  f"(channels={len(a.get('channels', []))})")

    # --- 拡張 ---
    ext = gltf.get("extensionsUsed", [])
    if ext:
        print(f"\n■ 使用glTF拡張")
        for e in ext:
            print(f"    {e}")
        if any("VRM" in e for e in ext):
            print("    → VRM拡張あり。表情プリセットが含まれる可能性")

    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()
