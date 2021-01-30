#ifndef BENTOBOX_POS2DCOMPONENT_H
#define BENTOBOX_POS2DCOMPONENT_H

#include <bento/protos/ecs.pb.h>
#include <component/userComponent.h>

namespace ics::component {
const char POS2D_COMPONENT_NAME[] = "Pos2DComponent";
}

namespace {

// This needs to be in the header as it is called immediately in the header as
// well.
bento::protos::ComponentDef createCompDef() {
    auto compDef = bento::protos::ComponentDef();
    compDef.set_name(ics::component::POS2D_COMPONENT_NAME);

    auto& schema = *compDef.mutable_schema();
    schema["x"] = bento::protos::Type();
    schema["x"].set_primitive(bento::protos::Type_Primitive_INT64);

    schema["y"] = bento::protos::Type();
    schema["y"].set_primitive(bento::protos::Type_Primitive_INT64);

    return compDef;
};

}  // namespace

namespace ics::component {
struct Pos2DComponent : public UserComponent {
    Pos2DComponent() : UserComponent(POS2D_COMPONENT_NAME, createCompDef()) {}
};
}  // namespace ics::component

#endif  // BENTOBOX_POS2DCOMPONENT_H
