import { onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import api from "@/utils/api";
const list = ref([]);
const loading = ref(false);
const filterRead = ref("");
const loadData = async () => {
    loading.value = true;
    try {
        const params = {};
        if (filterRead.value === "read")
            params.is_read = 1;
        if (filterRead.value === "unread")
            params.is_read = 0;
        const res = await api.get("/member/notifications", { params });
        const payload = res.data;
        if (Array.isArray(payload)) {
            list.value = payload;
        }
        else if (payload?.items && Array.isArray(payload.items)) {
            list.value = payload.items;
        }
        else if (payload?.data && Array.isArray(payload.data)) {
            list.value = payload.data;
        }
        else {
            list.value = [];
        }
    }
    catch (e) {
        ElMessage.error(e?.response?.data?.detail || "加载通知失败");
    }
    finally {
        loading.value = false;
    }
};
const markRead = async (row) => {
    try {
        await api.put(`/member/notifications/${row.id}/read`);
        row.is_read = 1;
        ElMessage.success("已标记为已读");
    }
    catch (e) {
        ElMessage.error(e?.response?.data?.detail || "操作失败");
    }
};
onMounted(loadData);
debugger; /* PartiallyEnd: #3632/scriptSetup.vue */
const __VLS_ctx = {
    ...{},
    ...{},
};
let __VLS_components;
let __VLS_directives;
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "page" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "page-header" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "page-header-title" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "page-header-subtitle" },
});
const __VLS_0 = {}.ElCard;
/** @type {[typeof __VLS_components.ElCard, typeof __VLS_components.elCard, typeof __VLS_components.ElCard, typeof __VLS_components.elCard, ]} */ ;
// @ts-ignore
ElCard;
// @ts-ignore
const __VLS_1 = __VLS_asFunctionalComponent(__VLS_0, new __VLS_0({
    shadow: "hover",
    ...{ class: "page-card" },
}));
const __VLS_2 = __VLS_1({
    shadow: "hover",
    ...{ class: "page-card" },
}, ...__VLS_functionalComponentArgsRest(__VLS_1));
const { default: __VLS_4 } = __VLS_3.slots;
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "filters" },
});
const __VLS_5 = {}.ElRadioGroup;
/** @type {[typeof __VLS_components.ElRadioGroup, typeof __VLS_components.elRadioGroup, typeof __VLS_components.ElRadioGroup, typeof __VLS_components.elRadioGroup, ]} */ ;
// @ts-ignore
ElRadioGroup;
// @ts-ignore
const __VLS_6 = __VLS_asFunctionalComponent(__VLS_5, new __VLS_5({
    ...{ 'onChange': {} },
    modelValue: (__VLS_ctx.filterRead),
    size: "small",
}));
const __VLS_7 = __VLS_6({
    ...{ 'onChange': {} },
    modelValue: (__VLS_ctx.filterRead),
    size: "small",
}, ...__VLS_functionalComponentArgsRest(__VLS_6));
let __VLS_9;
let __VLS_10;
const __VLS_11 = ({ change: {} },
    { onChange: (__VLS_ctx.loadData) });
const { default: __VLS_12 } = __VLS_8.slots;
// @ts-ignore
[filterRead, loadData,];
const __VLS_13 = {}.ElRadioButton;
/** @type {[typeof __VLS_components.ElRadioButton, typeof __VLS_components.elRadioButton, typeof __VLS_components.ElRadioButton, typeof __VLS_components.elRadioButton, ]} */ ;
// @ts-ignore
ElRadioButton;
// @ts-ignore
const __VLS_14 = __VLS_asFunctionalComponent(__VLS_13, new __VLS_13({
    label: (''),
}));
const __VLS_15 = __VLS_14({
    label: (''),
}, ...__VLS_functionalComponentArgsRest(__VLS_14));
const { default: __VLS_17 } = __VLS_16.slots;
var __VLS_16;
const __VLS_18 = {}.ElRadioButton;
/** @type {[typeof __VLS_components.ElRadioButton, typeof __VLS_components.elRadioButton, typeof __VLS_components.ElRadioButton, typeof __VLS_components.elRadioButton, ]} */ ;
// @ts-ignore
ElRadioButton;
// @ts-ignore
const __VLS_19 = __VLS_asFunctionalComponent(__VLS_18, new __VLS_18({
    label: "unread",
}));
const __VLS_20 = __VLS_19({
    label: "unread",
}, ...__VLS_functionalComponentArgsRest(__VLS_19));
const { default: __VLS_22 } = __VLS_21.slots;
var __VLS_21;
const __VLS_23 = {}.ElRadioButton;
/** @type {[typeof __VLS_components.ElRadioButton, typeof __VLS_components.elRadioButton, typeof __VLS_components.ElRadioButton, typeof __VLS_components.elRadioButton, ]} */ ;
// @ts-ignore
ElRadioButton;
// @ts-ignore
const __VLS_24 = __VLS_asFunctionalComponent(__VLS_23, new __VLS_23({
    label: "read",
}));
const __VLS_25 = __VLS_24({
    label: "read",
}, ...__VLS_functionalComponentArgsRest(__VLS_24));
const { default: __VLS_27 } = __VLS_26.slots;
var __VLS_26;
var __VLS_8;
const __VLS_28 = {}.ElTable;
/** @type {[typeof __VLS_components.ElTable, typeof __VLS_components.elTable, typeof __VLS_components.ElTable, typeof __VLS_components.elTable, ]} */ ;
// @ts-ignore
ElTable;
// @ts-ignore
const __VLS_29 = __VLS_asFunctionalComponent(__VLS_28, new __VLS_28({
    data: (__VLS_ctx.list),
    border: true,
    ...{ style: {} },
    size: "small",
}));
const __VLS_30 = __VLS_29({
    data: (__VLS_ctx.list),
    border: true,
    ...{ style: {} },
    size: "small",
}, ...__VLS_functionalComponentArgsRest(__VLS_29));
__VLS_asFunctionalDirective(__VLS_directives.vLoading)(null, { ...__VLS_directiveBindingRestFields, value: (__VLS_ctx.loading) }, null, null);
const { default: __VLS_32 } = __VLS_31.slots;
// @ts-ignore
[list, vLoading, loading,];
const __VLS_33 = {}.ElTableColumn;
/** @type {[typeof __VLS_components.ElTableColumn, typeof __VLS_components.elTableColumn, ]} */ ;
// @ts-ignore
ElTableColumn;
// @ts-ignore
const __VLS_34 = __VLS_asFunctionalComponent(__VLS_33, new __VLS_33({
    prop: "title",
    label: "标题",
    minWidth: "180",
}));
const __VLS_35 = __VLS_34({
    prop: "title",
    label: "标题",
    minWidth: "180",
}, ...__VLS_functionalComponentArgsRest(__VLS_34));
const __VLS_38 = {}.ElTableColumn;
/** @type {[typeof __VLS_components.ElTableColumn, typeof __VLS_components.elTableColumn, ]} */ ;
// @ts-ignore
ElTableColumn;
// @ts-ignore
const __VLS_39 = __VLS_asFunctionalComponent(__VLS_38, new __VLS_38({
    prop: "content",
    label: "内容",
    minWidth: "280",
}));
const __VLS_40 = __VLS_39({
    prop: "content",
    label: "内容",
    minWidth: "280",
}, ...__VLS_functionalComponentArgsRest(__VLS_39));
const __VLS_43 = {}.ElTableColumn;
/** @type {[typeof __VLS_components.ElTableColumn, typeof __VLS_components.elTableColumn, ]} */ ;
// @ts-ignore
ElTableColumn;
// @ts-ignore
const __VLS_44 = __VLS_asFunctionalComponent(__VLS_43, new __VLS_43({
    prop: "created_at",
    label: "时间",
    width: "170",
}));
const __VLS_45 = __VLS_44({
    prop: "created_at",
    label: "时间",
    width: "170",
}, ...__VLS_functionalComponentArgsRest(__VLS_44));
const __VLS_48 = {}.ElTableColumn;
/** @type {[typeof __VLS_components.ElTableColumn, typeof __VLS_components.elTableColumn, typeof __VLS_components.ElTableColumn, typeof __VLS_components.elTableColumn, ]} */ ;
// @ts-ignore
ElTableColumn;
// @ts-ignore
const __VLS_49 = __VLS_asFunctionalComponent(__VLS_48, new __VLS_48({
    prop: "is_read",
    label: "状态",
    width: "120",
}));
const __VLS_50 = __VLS_49({
    prop: "is_read",
    label: "状态",
    width: "120",
}, ...__VLS_functionalComponentArgsRest(__VLS_49));
const { default: __VLS_52 } = __VLS_51.slots;
{
    const { default: __VLS_53 } = __VLS_51.slots;
    const [{ row }] = __VLS_getSlotParameters(__VLS_53);
    const __VLS_54 = {}.ElTag;
    /** @type {[typeof __VLS_components.ElTag, typeof __VLS_components.elTag, typeof __VLS_components.ElTag, typeof __VLS_components.elTag, ]} */ ;
    // @ts-ignore
    ElTag;
    // @ts-ignore
    const __VLS_55 = __VLS_asFunctionalComponent(__VLS_54, new __VLS_54({
        size: "small",
        type: (row.is_read ? 'info' : 'success'),
    }));
    const __VLS_56 = __VLS_55({
        size: "small",
        type: (row.is_read ? 'info' : 'success'),
    }, ...__VLS_functionalComponentArgsRest(__VLS_55));
    const { default: __VLS_58 } = __VLS_57.slots;
    (row.is_read ? "已读" : "未读");
    var __VLS_57;
}
var __VLS_51;
const __VLS_59 = {}.ElTableColumn;
/** @type {[typeof __VLS_components.ElTableColumn, typeof __VLS_components.elTableColumn, typeof __VLS_components.ElTableColumn, typeof __VLS_components.elTableColumn, ]} */ ;
// @ts-ignore
ElTableColumn;
// @ts-ignore
const __VLS_60 = __VLS_asFunctionalComponent(__VLS_59, new __VLS_59({
    label: "操作",
    width: "120",
}));
const __VLS_61 = __VLS_60({
    label: "操作",
    width: "120",
}, ...__VLS_functionalComponentArgsRest(__VLS_60));
const { default: __VLS_63 } = __VLS_62.slots;
{
    const { default: __VLS_64 } = __VLS_62.slots;
    const [{ row }] = __VLS_getSlotParameters(__VLS_64);
    if (!row.is_read) {
        const __VLS_65 = {}.ElButton;
        /** @type {[typeof __VLS_components.ElButton, typeof __VLS_components.elButton, typeof __VLS_components.ElButton, typeof __VLS_components.elButton, ]} */ ;
        // @ts-ignore
        ElButton;
        // @ts-ignore
        const __VLS_66 = __VLS_asFunctionalComponent(__VLS_65, new __VLS_65({
            ...{ 'onClick': {} },
            link: true,
            type: "primary",
            size: "small",
        }));
        const __VLS_67 = __VLS_66({
            ...{ 'onClick': {} },
            link: true,
            type: "primary",
            size: "small",
        }, ...__VLS_functionalComponentArgsRest(__VLS_66));
        let __VLS_69;
        let __VLS_70;
        const __VLS_71 = ({ click: {} },
            { onClick: (...[$event]) => {
                    if (!(!row.is_read))
                        return;
                    __VLS_ctx.markRead(row);
                    // @ts-ignore
                    [markRead,];
                } });
        const { default: __VLS_72 } = __VLS_68.slots;
        var __VLS_68;
    }
    else {
        __VLS_asFunctionalElement(__VLS_intrinsics.span, __VLS_intrinsics.span)({
            ...{ class: "muted" },
        });
    }
}
var __VLS_62;
var __VLS_31;
if (!__VLS_ctx.loading && !__VLS_ctx.list.length) {
    // @ts-ignore
    [list, loading,];
    __VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "empty" },
    });
}
var __VLS_3;
/** @type {__VLS_StyleScopedClasses['page']} */ ;
/** @type {__VLS_StyleScopedClasses['page-header']} */ ;
/** @type {__VLS_StyleScopedClasses['page-header-title']} */ ;
/** @type {__VLS_StyleScopedClasses['page-header-subtitle']} */ ;
/** @type {__VLS_StyleScopedClasses['page-card']} */ ;
/** @type {__VLS_StyleScopedClasses['filters']} */ ;
/** @type {__VLS_StyleScopedClasses['muted']} */ ;
/** @type {__VLS_StyleScopedClasses['empty']} */ ;
const __VLS_export = (await import('vue')).defineComponent({});
export default {};
