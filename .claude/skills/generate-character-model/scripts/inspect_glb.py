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
    """GLB(バイナリ)とglTF(JSON)の両方を読めるようにする。
    バイナリチャンクも返す(バインドポーズの算出に使う)。"""
    with open(path, "rb") as f:
        head = f.read(4)
        f.seek(0)
        if head == b"glTF":
            magic, version, _ = struct.unpack("<III", f.read(12))
            gltf = binc = None
            while True:
                h = f.read(8)
                if len(h) < 8:
                    break
                clen, ctype = struct.unpack("<II", h)
                chunk = f.read(clen)
                if ctype == 0x4E4F534A:      # JSON
                    gltf = json.loads(chunk.decode("utf-8"))
                elif ctype == 0x004E4942:    # BIN
                    binc = chunk
            if gltf is None:
                raise ValueError("GLBにJSONチャンクが見つからない")
            return gltf, version, binc
        return json.load(open(path, encoding="utf-8")), None, None


def _inv_affine_translation(m):
    """列優先4x4アフィン行列の逆行列の平行移動成分を返す。
    inverse bind matrix を逆変換すると、メッシュ空間でのボーン位置が得られる。
    回転を含めて正しく求まるため、平行移動だけを累積するより信頼できる。"""
    a = [[m[0], m[4], m[8]], [m[1], m[5], m[9]], [m[2], m[6], m[10]]]
    t = [m[12], m[13], m[14]]
    det = (a[0][0] * (a[1][1] * a[2][2] - a[1][2] * a[2][1])
           - a[0][1] * (a[1][0] * a[2][2] - a[1][2] * a[2][0])
           + a[0][2] * (a[1][0] * a[2][1] - a[1][1] * a[2][0]))
    if abs(det) < 1e-12:
        return None
    inv = [[0.0] * 3 for _ in range(3)]
    inv[0][0] = (a[1][1] * a[2][2] - a[1][2] * a[2][1]) / det
    inv[0][1] = (a[0][2] * a[2][1] - a[0][1] * a[2][2]) / det
    inv[0][2] = (a[0][1] * a[1][2] - a[0][2] * a[1][1]) / det
    inv[1][0] = (a[1][2] * a[2][0] - a[1][0] * a[2][2]) / det
    inv[1][1] = (a[0][0] * a[2][2] - a[0][2] * a[2][0]) / det
    inv[1][2] = (a[0][2] * a[1][0] - a[0][0] * a[1][2]) / det
    inv[2][0] = (a[1][0] * a[2][1] - a[1][1] * a[2][0]) / det
    inv[2][1] = (a[0][1] * a[2][0] - a[0][0] * a[2][1]) / det
    inv[2][2] = (a[0][0] * a[1][1] - a[0][1] * a[1][0]) / det
    return [-(inv[r][0] * t[0] + inv[r][1] * t[1] + inv[r][2] * t[2]) for r in range(3)]


def mouth_anchor(gltf, binc, pos, joint_names):
    """口を重ねる位置(鼻先)をメッシュとボーンから導出する。

    リップシンクは3Dの口を動かすのではなく、headボーンに親子付けした板を
    重ねて表現する方針のため、その取り付け位置が要る。顔の向きは
    frontleg/backlegボーンのどちら側が前かで判定し、headボーン近傍で
    最も前方にある頂点を鼻先とみなす。

    戻り値: (アンカー座標, バウンディングボックス内の相対位置, メッシュ最大寸法)
    """
    head = next((p for n, p in zip(joint_names, pos) if n.lower() == "head"), None)
    front = [p for n, p in zip(joint_names, pos) if "frontleg" in n.lower()]
    back = [p for n, p in zip(joint_names, pos) if "backleg" in n.lower()]
    if head is None or not front or not back:
        return None

    # 前後の軸と向きを、脚ボーンの配置から決める
    axis, sign, best = 2, 1, 0.0
    for ax in range(3):
        d = sum(v[ax] for v in front) / len(front) - sum(v[ax] for v in back) / len(back)
        if abs(d) > abs(best):
            axis, sign, best = ax, (1 if d > 0 else -1), d

    prim = gltf["meshes"][0]["primitives"][0]
    pa = gltf["accessors"][prim["attributes"]["POSITION"]]
    if not pa.get("min") or not pa.get("max"):
        return None
    bv = gltf["bufferViews"][pa["bufferView"]]
    off = bv.get("byteOffset", 0) + pa.get("byteOffset", 0)
    stride = bv.get("byteStride") or 12
    try:
        verts = [struct.unpack_from("<3f", binc, off + i * stride)
                 for i in range(pa["count"])]
    except struct.error:
        return None

    mn, mx = pa["min"], pa["max"]
    size = max(mx[i] - mn[i] for i in range(3))
    r2 = (size * 0.25) ** 2
    near = [v for v in verts
            if sum((v[i] - head[i]) ** 2 for i in range(3)) <= r2]
    if not near:
        return None

    tip = max(near, key=lambda v: v[axis] * sign)
    rel = [(tip[i] - mn[i]) / (mx[i] - mn[i]) if mx[i] > mn[i] else 0.5
           for i in range(3)]
    return tip, rel, size, "XYZ"[axis], sign


def bone_positions(gltf, binc):
    """各ボーンのバインドポーズ位置を {ノード番号: (x,y,z)} で返す"""
    if not binc or not gltf.get("skins"):
        return {}
    skin = gltf["skins"][0]
    ibm = skin.get("inverseBindMatrices")
    if ibm is None:
        return {}
    acc = gltf["accessors"][ibm]
    bv = gltf["bufferViews"][acc["bufferView"]]
    off = bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
    out = {}
    for i, ji in enumerate(skin.get("joints", [])):
        try:
            m = list(struct.unpack_from("<16f", binc, off + i * 64))
        except struct.error:
            break
        p = _inv_affine_translation(m)
        if p:
            out[ji] = p
    return out


def main():
    if len(sys.argv) < 2:
        sys.exit("使い方: python3 scripts/inspect_glb.py <path-to.glb>")
    path = sys.argv[1]
    if not os.path.exists(path):
        sys.exit(f"ファイルが見つからない: {path}")

    gltf, version, binc = load_gltf(path)
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
    joint_ids = []
    for skin in skins:
        joint_ids.extend(j for j in skin.get("joints", []) if j < len(nodes))
    joints = [nodes[j].get("name", f"<node{j}>") for j in joint_ids]

    # バインドポーズ位置。ボーン名が無名(Bone_000 等)でも位置から判断できる
    pos = bone_positions(gltf, binc)

    # メッシュのバウンディングボックス(位置の解釈に使う)
    bbox = None
    for m in meshes:
        for p in m.get("primitives", []):
            pa = p.get("attributes", {}).get("POSITION")
            if pa is not None and pa < len(accessors):
                a = accessors[pa]
                if a.get("min") and a.get("max"):
                    bbox = (a["min"], a["max"])
                    break
        if bbox:
            break

    parent = {}
    for i, n in enumerate(nodes):
        for c in n.get("children", []):
            parent[c] = i

    print(f"\n■ ボーン構成 ({len(joints)}個)")
    if joint_ids:
        for j in joint_ids:
            name = nodes[j].get("name", f"<node{j}>")
            p = parent.get(j)
            pname = nodes[p].get("name", f"<{p}>") if p is not None else "(root)"
            if j in pos:
                x, y, z = pos[j]
                print(f"    {name:<16} 親={pname:<16} X={x:>7.3f} Y={y:>7.3f} Z={z:>7.3f}")
            else:
                print(f"    {name:<16} 親={pname}")
    else:
        print("    ボーンなし(リグが適用されていない)")

    if bbox:
        mn, mx = bbox
        print(f"\n  メッシュ範囲  X:{mn[0]:.3f}〜{mx[0]:.3f}"
              f"  Y:{mn[1]:.3f}〜{mx[1]:.3f}  Z:{mn[2]:.3f}〜{mx[2]:.3f}")

    # --- 核心判定1: 顎まわり ---
    jaw_keys = ("jaw", "mouth", "chin", "tongue", "lip", "teeth")
    jaw_hits = [n for n in joints if any(k in n.lower() for k in jaw_keys)]
    print(f"\n■ 【核心1】顎・口まわりのボーン")
    if jaw_hits:
        for n in jaw_hits:
            print(f"    ✓ {n}")
        print("    → 顎ボーン回転+音声振幅によるリップシンクが可能")
    else:
        print("    ✗ 名前の一致なし")
        anon = [n for n in joints if n.lower().startswith("bone_") or n.startswith("<node")]
        if anon and pos and bbox:
            # 無名リグの場合、頭部帯にどのボーンがあるかを見せて人が判断できるようにする
            mn, mx = bbox
            head_y = mn[1] + (mx[1] - mn[1]) * 0.75
            head = [(nodes[j].get("name", f"<{j}>"), pos[j])
                    for j in joint_ids if j in pos and pos[j][1] >= head_y]
            print(f"\n    ボーン名が無名のため、名前では判定できない。")
            print(f"    頭部相当の高さ帯 (Y >= {head_y:.3f}) にあるボーン:")
            for n, p in sorted(head, key=lambda r: -r[1][1]):
                print(f"      {n:<16} X={p[0]:>7.3f} Y={p[1]:>7.3f} Z={p[2]:>7.3f}")
            if not head:
                print("      なし")
            print("\n    左右対称に並ぶ対は耳や目の可能性が高い。口は顔の前面")
            print("    (Zが正面側)かつ頭の中心より下にあるはず。該当がなければ")
            print("    顎ボーンは生成されていない。")
        else:
            print("    → 顎ボーン方式は不可。プロシージャルな頂点変形か、")
            print("       アーキタイプ側で顔リグを作り込む(方式b)必要がある")

    head_hits = [n for n in joints if "head" in n.lower() or "neck" in n.lower()]
    print(f"\n■ 頭・首ボーン(視線/頷きの制御に使う)")
    print(f"    {head_hits if head_hits else '✗ 名前の一致なし(上の位置情報から判断する)'}")

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

    # --- 口を重ねる位置 ---
    print(f"\n■ 口のアンカー(リップシンク用の板を取り付ける位置)")
    anchor = None
    if joint_ids and pos and binc:
        names = [nodes[j].get("name", str(j)) for j in joint_ids]
        plist = [pos.get(j) for j in joint_ids]
        if all(p is not None for p in plist):
            anchor = mouth_anchor(gltf, binc, plist, names)
    if anchor:
        tip, rel, size, axis, sign = anchor
        print(f"    顔の向き   : {'+' if sign > 0 else '-'}{axis} (脚ボーンの配置から判定)")
        print(f"    アンカー座標: ({tip[0]:.4f}, {tip[1]:.4f}, {tip[2]:.4f})")
        print(f"    BBox内の相対位置: X={rel[0]:.1%} Y={rel[1]:.1%} Z={rel[2]:.1%}")
        print(f"    メッシュ最大寸法: {size:.4f}")
        print(f"    → 板の寸法目安(寸法比): 6%={size*0.06:.4f} 8%={size*0.08:.4f}")
        if abs(rel[0] - 0.5) < 0.05:
            print(f"    ✓ Xがほぼ50%。正中線上にあり妥当な鼻先とみなせる")
        else:
            print(f"    ⚠ Xが50%から外れている。左右非対称な形状か、導出が外れた可能性")
        print("    ※ 寸法は必ずメッシュ寸法比で指定する。モデルは極端に小さい")
        print("      スケール(この例で最大0.0167)で書き出されることがあり、")
        print("      絶対値で指定すると別キャラで破綻する")
    else:
        print("    導出不可(head / frontleg / backleg ボーンが揃っていない)")

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
