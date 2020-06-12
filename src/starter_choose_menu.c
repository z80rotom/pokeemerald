#include "global.h" // Must be loaded in first, 
// because other files don't include it for some reason.

#include "bg.h" // LoadBgTiles 
#include "decompress.h" // LZDecompressWram
#include "graphics.h"
#include "main.h"
#include "menu.h"
#include "menu_helpers.h"
#include "palette.h"
#include "pokemon.h"
#include "pokemon_icon.h"
#include "constants/species.h"
#include "scanline_effect.h"
#include "starter_choose_menu.h"

#define STARTER_MON_COUNT   6

// static const u8 sStarterChooseSpriteCoords[STARTER_MON_COUNT][2] =
// {
//     { {20, 20}, {60, 20}, {100, 20}, {140, 20}, {180, 20}, {220, 20} }
// };

static const struct WindowTemplate sSinglePartyMenuWindowTemplate[] =
{
    {
        .bg = 0,
        .tilemapLeft = 1,
        .tilemapTop = 3,
        .width = 10,
        .height = 7,
        .paletteNum = 3,
        .baseBlock = 0x63,
    },
    {
        .bg = 0,
        .tilemapLeft = 12,
        .tilemapTop = 1,
        .width = 18,
        .height = 3,
        .paletteNum = 4,
        .baseBlock = 0xA9,
    },
    {
        .bg = 0,
        .tilemapLeft = 12,
        .tilemapTop = 4,
        .width = 18,
        .height = 3,
        .paletteNum = 5,
        .baseBlock = 0xDF,
    },
    {
        .bg = 0,
        .tilemapLeft = 12,
        .tilemapTop = 7,
        .width = 18,
        .height = 3,
        .paletteNum = 6,
        .baseBlock = 0x115,
    },
    {
        .bg = 0,
        .tilemapLeft = 12,
        .tilemapTop = 10,
        .width = 18,
        .height = 3,
        .paletteNum = 7,
        .baseBlock = 0x14B,
    },
    {
        .bg = 0,
        .tilemapLeft = 12,
        .tilemapTop = 13,
        .width = 18,
        .height = 3,
        .paletteNum = 8,
        .baseBlock = 0x181,
    },
    {
        .bg = 2,
        .tilemapLeft = 1,
        .tilemapTop = 15,
        .width = 28,
        .height = 4,
        .paletteNum = 14,
        .baseBlock = 0x1DF,
    },
    DUMMY_WIN_TEMPLATE
};

static EWRAM_DATA u8 *sPartyBgGfxTilemap = NULL;
static EWRAM_DATA u8 *sPartyBgTilemapBuffer = NULL;

static struct Pokemon sStarterPokemon[STARTER_MON_COUNT] = { 0 };

static const u16 sStarterSpecies[STARTER_MON_COUNT] = {
    SPECIES_TREECKO,
    SPECIES_TORCHIC,
    SPECIES_MUDKIP,
    SPECIES_CACNEA,
    SPECIES_SLUGMA,
    SPECIES_CORPHISH,
};

static bool8 ShowStarterChooseMenu(void);

void CB2_InitStarterChooseMenu(void)
{
    while (TRUE)
    {
        if ( MenuHelpers_CallLinkSomething() == TRUE || ShowStarterChooseMenu() == TRUE || MenuHelpers_CallLinkSomething() == TRUE )
            break;
    }
}

static void CreateStarterMonIconSpriteParameterized(u16 species, u32 pid, u8 priority, bool32 handleDeoxys)
{
    u8 monSpriteId;
    if (species != SPECIES_NONE)
    {
        monSpriteId = CreateMonIcon(species, SpriteCB_MonIcon, 20, 20, 4, pid, handleDeoxys);
        gSprites[monSpriteId].oam.priority = priority;
    }
}

static void CreateStarterMonIconSprite() // struct Pokemon *mon, const u8 * spriteCoords)
{
    bool32 handleDeoxys = TRUE;
    u16 species2;
    u32 personality;

    // species2 = GetMonData(mon, MON_DATA_SPECIES2);
    // personality = GetMonData(mon, MON_DATA_PERSONALITY);
    CreateStarterMonIconSpriteParameterized(SPECIES_MUDKIP, 0, 1, handleDeoxys);
}

static void CreateStarterMonSprites()
{
    for (int i = 0; i < STARTER_MON_COUNT; i++)
    {
        CreateStarterMonIconSprite(); // &sStarterPokemon[i] , &sStarterChooseSpriteCoords[i]);
    }
}

static void CreateStarterPokemon() 
{
    for (int i = 0; i < STARTER_MON_COUNT; i++)
    {
        SetMonData(&sStarterPokemon[i], MON_DATA_SPECIES, &sStarterSpecies[i]);
    }
}

static void VBlankCB_StarterChooseMenu(void)
{
    LoadOam();
    ProcessSpriteCopyRequests();
    TransferPlttBuffer();
}

static void CB2_UpdateStarterChooseMenu(void)
{
    RunTasks();
    AnimateSprites();
    BuildOamBuffer();
    do_scheduled_bg_tilemap_copies_to_vram();
    UpdatePaletteFade();
}

static void InitStarterChooseWindow()
{
    InitWindows(sSinglePartyMenuWindowTemplate);

    DeactivateAllTextPrinters();
    for (int i = 0; i < 6; i++)
        FillWindowPixelBuffer(i, PIXEL_FILL(0));
    LoadUserWindowBorderGfx(0, 0x4F, 0xD0);
    LoadPalette(GetOverworldTextboxPalettePtr(), 0xE0, 0x20);
    LoadPalette(gUnknown_0860F074, 0xF0, 0x20);
}

static void allocBgGfx()
{
    u32 sizeout;
    sPartyBgGfxTilemap = malloc_and_decompress(gPartyMenuBg_Gfx, &sizeout);
    LoadBgTiles(1, sPartyBgGfxTilemap, sizeout, 0);

    LZDecompressWram(gPartyMenuBg_Tilemap, sPartyBgTilemapBuffer);
    // sPartyMenuInternal->data[0]++;

    LoadCompressedPalette(gPartyMenuBg_Pal, 0, 0x160);
    // CpuCopy16(gPlttBufferUnfaded, sPartyMenuInternal->palBuffer, 0x160);
    // sPartyMenuInternal->data[0]++;
}

bool8 ShowStarterChooseMenu(void)
{
    switch (gMain.state)
    {
        case 0:
            SetVBlankHBlankCallbacksToNull();
            ResetVramOamAndBgCntRegs();
            clear_scheduled_bg_copies_to_vram();
            gMain.state++;
            break;
        case 1:
            ScanlineEffect_Stop();
            gMain.state++;
            break;
        case 2:
            ResetPaletteFade();
            gPaletteFade.bufferTransferDisabled = TRUE;
            gMain.state++;
            break;
        case 3:
            ResetSpriteData();
            gMain.state++;
            break;
        case 4:
            FreeAllSpritePalettes();
            gMain.state++;
            break;
        case 5:
            if (!MenuHelpers_LinkSomething())
                ResetTasks();
            gMain.state++;
            break;
        case 6:
            // CreateStarterPokemon();
            gMain.state++;
            break;
        case 7:
            LoadMonIconPalettes();
            gMain.state++;
            break;
        case 8:
            CreateStarterMonSprites();
            gMain.state++;
            break;
        case 9:
            allocBgGfx();
            gMain.state++;
            break;
        case 10:
            InitStarterChooseWindow();
            gMain.state++;
        default:
            SetVBlankCallback(VBlankCB_StarterChooseMenu);
            SetMainCallback2(CB2_UpdateStarterChooseMenu);
            return TRUE;
    }
    return FALSE;
}